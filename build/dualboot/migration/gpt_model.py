"""Pure, constrained lmi GPT transformation. No device access."""
import struct,uuid,zlib
SECTOR=4096
DISK_BYTES=254669750272
def crc(b):return zlib.crc32(b)&0xffffffff
def header(raw,location):
    if len(raw)!=SECTOR or raw[:8]!=b'EFI PART':raise ValueError('Invalid GPT header')
    revision,size,saved=struct.unpack_from('<III',raw,8)
    if revision!=0x10000 or size!=92:raise ValueError('Unreviewed GPT revision/size')
    h=bytearray(raw[:size]);h[16:20]=b'\0'*4
    if crc(h)!=saved:raise ValueError('GPT header CRC mismatch')
    current,other,first,last=struct.unpack_from('<4Q',raw,24)
    table,count,entry_size,table_crc=struct.unpack_from('<QIII',raw,72)
    if current!=location or count!=64 or entry_size!=128:raise ValueError('Unexpected GPT geometry')
    return dict(current=current,other=other,first=first,last=last,table=table,count=count,entry_size=entry_size,table_crc=table_crc)
def entries(table):
    result=[]
    for i in range(64):
        e=table[i*128:(i+1)*128]
        if e[:16]==b'\0'*16:
            if e.strip(b'\0'):raise ValueError('Nonempty unused entry')
            continue
        start,end,attrs=struct.unpack_from('<QQQ',e,32)
        if start>end:raise ValueError('Invalid partition bounds')
        result.append(dict(number=i+1,start_lba=start,end_lba=end,attributes=attrs,label=e[56:128].decode('utf-16le').rstrip('\0')))
    return result
def build(primary,backup,table,backup_table,expected):
    last=DISK_BYTES//SECTOR-1;p=header(primary,1);b=header(backup,last)
    if p['other']!=last or b['other']!=1 or p['first']!=6 or p['last']!=last-5:raise ValueError('Unexpected usable range')
    if b['first']!=p['first'] or b['last']!=p['last'] or primary[56:72]!=backup[56:72]:raise ValueError('GPT copies disagree')
    # Xiaomi retains four reserved sectors for each entry-array area even
    # though this header declares only 64*128 bytes (two populated sectors).
    if p['table']!=2 or b['table']!=last-4:raise ValueError('Unexpected table locations')
    if len(table)!=8192 or table!=backup_table or crc(table)!=p['table_crc'] or crc(table)!=b['table_crc']:raise ValueError('GPT table copies/CRCs disagree')
    old=entries(table)
    if old!=expected['entries'] or expected['sector_bytes']!=SECTOR:raise ValueError('Layout changed since qualified Mobian read')
    if len(old)!=34 or old[-1]['number']!=34 or old[-1]['label']!='userdata' or old[-1]['end_lba']!=p['last']:raise ValueError('Unexpected userdata layout')
    ordered=sorted(old,key=lambda e:e['start_lba'])
    if any(a['end_lba']>=b['start_lba'] for a,b in zip(ordered,ordered[1:])):raise ValueError('Overlapping source partitions')
    if table[34*128:35*128].strip(b'\0'):raise ValueError('Entry 35 already occupied')
    size=16*1024**3//SECTOR;start=(p['last']+1-size)//256*256;end=start+size-1
    if start<=old[-1]['start_lba'] or end>p['last']:raise ValueError('Insufficient space')
    new=bytearray(table);struct.pack_into('<Q',new,33*128+40,start-1)
    e=bytearray(128);e[:16]=uuid.UUID('0fc63daf-8483-4772-8e79-3d69d8477de4').bytes_le
    e[16:32]=uuid.uuid4().bytes_le;struct.pack_into('<QQQ',e,32,start,end,0)
    name='mobian'.encode('utf-16le');e[56:56+len(name)]=name;new[34*128:35*128]=e
    # Check every byte outside the specifically allowed fields remains identical.
    check=bytearray(new);check[33*128+40:33*128+48]=table[33*128+40:33*128+48];check[34*128:35*128]=table[34*128:35*128]
    if check!=table:raise ValueError('Unexpected table modification')
    def update(raw):
        h=bytearray(raw);struct.pack_into('<I',h,88,crc(new));h[16:20]=b'\0'*4;struct.pack_into('<I',h,16,crc(h[:92]));return bytes(h)
    ph,bh=update(primary),update(backup)
    header(ph,1);header(bh,last)
    plan={'userdata_new_end_lba':start-1,'mobian_start_lba':start,'mobian_end_lba':end,'mobian_bytes':size*SECTOR,'sector_bytes':SECTOR,'data_reformat_required':True}
    return [(b['table'],bytes(new)),(last,bh),(p['table'],bytes(new)),(1,ph)],plan
