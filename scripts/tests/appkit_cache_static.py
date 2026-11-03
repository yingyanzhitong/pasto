"""Read selected installed arm64e AppKit cache metadata; never load/execute AppKit."""
from pathlib import Path
import hashlib,struct

class AppKitCacheStatic:
    def __init__(self):
        self.files=[];self.maps=[]
        root=Path('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld')
        for name in ['dyld_shared_cache_arm64e','dyld_shared_cache_arm64e.01']:
            p=root/name;f=p.open('rb');header=f.read(128);assert header.startswith(b'dyld_v1');offset,count=struct.unpack_from('<II',header,16);i=len(self.files);self.files.append(dict(path=str(p),handle=f,uuid=header[88:104].hex(),size=p.stat().st_size));f.seek(offset)
            for _ in range(count):
                vm,size,off,_,_=struct.unpack('<QQQII',f.read(32));self.maps.append(dict(vmaddr=vm,size=size,fileoff=off,cache=i))
    def close(self):
        for f in self.files:f['handle'].close()
    def read(self,a,size):
        m=next(m for m in self.maps if m['vmaddr']<=a and a+size<=m['vmaddr']+m['size']);f=self.files[m['cache']]['handle'];f.seek(m['fileoff']+a-m['vmaddr']);data=f.read(size)
        if len(data)!=size:raise ValueError('Truncated cache block')
        return data
    def u32(self,a):return struct.unpack('<I',self.read(a,4))[0]
    def u64(self,a):return struct.unpack('<Q',self.read(a,8))[0]
    def relative(self,a):return a+struct.unpack('<i',self.read(a,4))[0]
    def pointer(self,a):
        v=self.u64(a);return 0 if v==0 else 0x180000000+(v&0xffffffff)
    def string(self,a):
        b=self.read(a,512);end=b.find(b'\0')
        if end<0:raise ValueError('Unbounded cache string')
        return b[:end].decode()
    def class_list(self):
        image=0x18496b000;assert self.u32(image)==0xfeedfacf;p=image+32;found=[]
        for _ in range(self.u32(image+16)):
            cmd,size=self.u32(p),self.u32(p+4)
            if cmd==0x19:
                for i in range(self.u32(p+64)):
                    s=p+72+i*80
                    if self.read(s,16).rstrip(b'\0')==b'__objc_classlist':found.append((self.u64(s+32),self.u64(s+40)))
            p+=size
        assert found==[(0x1e6c36240,0x5050)]
        return found[0]
    def class_record(self,wanted):
        start,size=self.class_list()
        for slot in range(start,start+size,8):
            cls=self.pointer(slot);ro=self.pointer(cls+32)&~7;name=self.string(self.pointer(ro+24))
            if name==wanted:
                superclass=self.pointer(cls+8);superro=self.pointer(superclass+32)&~7
                return dict(slot=hex(slot),address=hex(cls),ro=hex(ro),name=name,superclass=hex(superclass),superclass_name=self.string(self.pointer(superro+24)))
        raise ValueError('AppKit class not found')
    def methods(self,record,wanted):
        lists=[];matches=[];ll=self.pointer(int(record['ro'],16)+32)&~3;size,count=self.u32(ll),self.u32(ll+4);assert size==8
        for i in range(count):
            entry=ll+8+i*8;raw=self.u64(entry);delta=raw>>16
            if delta&(1<<47):delta-=1<<48
            ml=entry+delta;flags,n=self.u32(ml),self.u32(ml+4);assert flags==0xc000000f;lists.append(dict(entry=hex(entry),raw=hex(raw),address=hex(ml),flags=hex(flags),count=n,sha256=hashlib.sha256(self.read(ml,8+n*12)).hexdigest()))
            for j in range(n):
                e=ml+8+j*12;name=self.string(0x1faac4f50+self.u32(e))
                if name==wanted:
                    imp=self.relative(e+8);matches.append(dict(entry=hex(e),name=name,types=self.string(self.relative(e+4)),imp=hex(imp),bytes=self.read(imp,8).hex()))
        return dict(list_list=hex(ll),list_count=count,lists=lists,matches=matches)
