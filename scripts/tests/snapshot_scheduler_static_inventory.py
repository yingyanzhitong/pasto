"""Enumerate this Mach-O image's SnapshotScheduler conformances without loading code."""
import hashlib,json,struct

def snapshot_scheduler_inventory(n):
    raw=n['raw'];pos=32;sections=[]
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        cmd,size=struct.unpack_from('<II',raw,pos)
        if cmd==0x19:
            for i in range(struct.unpack_from('<I',raw,pos+64)[0]):
                s=pos+72+i*80;name=raw[s:s+16].split(b'\0')[0]
                if name==b'__swift5_proto':sections.append(struct.unpack_from('<QQ',raw,s+32))
        pos+=size
    assert len(sections)==1
    start,size=sections[0];cache={};matches=[];rows=[];f=n['fixup'][0];h=struct.unpack_from('<7I',raw,f);assert h[5]==1
    for a in range(start,start+size,4):
        c=a+struct.unpack('<i',n['read'](a,4))[0];d=struct.unpack('<i',n['read'](c,4))[0];p=c+(d&~1)
        if d&1:
            if p not in cache:
                v,_=n['reachable_pointer'](p)
                if v>>63:
                    w=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];s=f+h[3]+(w>>9);cache[p]=raw[s:raw.index(b'\0',s)].decode()
                else:cache[p]=n['base']+(v&((1<<36)-1))
            p=cache[p]
        row=dict(entry=hex(a),conformance=hex(c),protocol=hex(p)if isinstance(p,int)else p);rows.append(row)
        if p==0x100cac844 or isinstance(p,str)and'SnapshotScheduler'in p:matches.append(row)
    return dict(section=hex(start),section_size=size,conformance_count=len(rows),indirect_pointer_count=len(cache),unresolved=0,matches=matches,projections_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest())
