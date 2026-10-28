#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Locate tentative source owners of historical SDK stubs without building."""
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    prior=json.loads((ROOT/'reports/replica/batch-pasto-sdk-completeness-15.json').read_text())
    records=prior['records'];names=[r['symbol'].removeprefix('_') for r in records]
    demangle=subprocess.run(['xcrun','swift-demangle','--compact'],input='\n'.join(names)+'\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    descriptions=demangle.stdout.splitlines()
    if len(descriptions)!=len(records):raise ValueError('无法逐符号对应demangle结果')
    files={str(p.relative_to(ROOT)):p.read_text() for p in (ROOT/'replica/Sources').rglob('*.swift')}
    changed=set(prior['changed_source_files']);added=set(prior['added_source_files']);rows=[];counts=Counter()
    for record,description in zip(records,descriptions):
        tokens=[]
        for x in re.findall(r'\b(?:Foundation|AppKit|SwiftUI|Combine|Carbon|Vision|CoreGraphics)\.([A-Za-z_][A-Za-z0-9_]*)',description):
            if len(x)>=4 and x not in {'Data','Date','String','Array','Bool','Error','UUID','URL','Int','Index','Set','CGFloat'} and x not in tokens:tokens.append(x)
        candidates=[]
        for token in tokens:
            pat=re.compile(r'\b'+re.escape(token)+r'\b')
            for path,text in files.items():
                match=pat.search(text)
                if match:candidates.append({'path':path,'line':text.count('\n',0,match.start())+1,'matched_owner':token,'file_status':'changed' if path in changed else 'added' if path in added else 'unchanged','source_sha256':hashlib.sha256(text.encode()).hexdigest()})
        candidates.sort(key=lambda x:(x['file_status']=='unchanged',x['path'],x['line']))
        counts['with_owner_name_candidate' if candidates else 'without_owner_name_candidate']+=1
        rows.append({'function_id':record['function_id'],'symbol':record['symbol'],'demangled':description,'owner_tokens':tokens,'candidate_count':len(candidates),'candidates':candidates[:8]})
    report={'kind':'static_sdk_source_owner_candidates','generated_at':datetime.now(timezone.utc).isoformat(),'policy':'仅通过demangle类型名与源码文本寻找优先检查的位置；名称命中不是调用证明、不判当前链接与等价，不提升迁移状态。','original_record_count':len(rows),'candidate_counts':dict(counts),'build_executed':False,'tests_executed':False,'product_executed':False,'records':rows}
    (ROOT/'reports/replica/batch-sdk-source-candidates-16.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))

if __name__=='__main__':main()
