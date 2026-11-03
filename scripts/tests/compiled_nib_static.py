"""Read compiled NIBArchive v1 tables as bytes; never instantiate archived classes."""
import struct

def decode_nib_archive(data):
    if len(data)<50 or data[:10]!=b'NIBArchive':raise ValueError('Not a NIBArchive')
    version,coder,no,oo,nk,ko,nv,vo,nc,co=struct.unpack_from('<10I',data,10)
    if version!=1 or not(50<=oo<=ko<=vo<=co<=len(data)):raise ValueError('Invalid NIB tables')
    def block(a,size):
        if size<0 or a<0 or a+size>len(data):raise ValueError('NIB data outside archive')
        return data[a:a+size]
    def varint(a):
        value=shift=0
        for _ in range(10):
            byte=block(a,1)[0];a+=1;value|=(byte&127)<<shift
            if byte&128:return value,a
            shift+=7
        raise ValueError('Invalid NIB varint')
    a=oo;objects=[]
    for _ in range(no):
        cls,a=varint(a);start,a=varint(a);count,a=varint(a);objects.append((cls,start,count))
    if a!=ko:raise ValueError('Object table size')
    keys=[]
    for _ in range(nk):
        size,a=varint(a);keys.append(block(a,size).decode());a+=size
    if a!=vo:raise ValueError('Key table size')
    values=[]
    for _ in range(nv):
        key,a=varint(a);tag=block(a,1)[0];a+=1
        if tag in [0,1,2,3,6,7,10]:
            fmt={0:'b',1:'h',2:'i',3:'q',6:'f',7:'d',10:'I'}[tag];size=struct.calcsize('<'+fmt);value=struct.unpack('<'+fmt,block(a,size))[0];a+=size
        elif tag in [4,5,9]:value={4:True,5:False,9:None}[tag]
        elif tag==8:size,a=varint(a);value=block(a,size);a+=size
        else:raise ValueError('Unknown NIB value type')
        if key>=nk or tag==10 and value>=no:raise ValueError('NIB reference outside table')
        values.append((keys[key],tag,value))
    if a!=co:raise ValueError('Value table size')
    classes=[]
    for _ in range(nc):
        size,a=varint(a);extra,a=varint(a);block(a,4*extra);a+=4*extra;name=block(a,size);a+=size;classes.append(name.rstrip(b'\0').decode())
    if a!=len(data):raise ValueError('Class table size')
    rows=[]
    for cls,start,count in objects:
        if cls>=nc or start+count>nv:raise ValueError('Invalid NIB object range')
        rows.append(dict(cls=classes[cls],values=values[start:start+count]))
    return dict(version=version,coder_version=coder,counts=dict(objects=no,keys=nk,values=nv,classes=nc),rows=rows)

def nib_string(archive,index):
    row=archive['rows'][index]
    if row['cls']!='NSString':raise ValueError('NIB string reference is not NSString')
    return next(v.decode()for k,t,v in row['values']if k=='NS.bytes'and t==8)
