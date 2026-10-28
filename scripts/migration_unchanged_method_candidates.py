#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify unchanged methods in changed files; candidates need consumer review."""
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def body(text,symbol):
    # Only a uniquely named function in a unique matching declaration is eligible.
    match=re.search(r'\b(f_100[0-9a-f]+)\b',symbol)
    if not match:return None
    name=match.group(1)
    lines=text.splitlines(keepends=True)
    start=[i for i,line in enumerate(lines) if re.search(r'\bfunc\s+'+re.escape(name)+r'\s*\(',line)]
    if len(start)!=1:return None
    start=start[0];depth=0;opened=False;result=[]
    for line in lines[start:]:
        result.append(line)
        # Strip simple quoted literals and line comments; reject multiline strings
        # and block comments instead of claiming a false match.
        if '"""' in line or '/*' in line or '*/' in line:return None
        stripped=re.sub(r'"(?:\\.|[^"\\])*"','""',line).split('//',1)[0]
        depth+=stripped.count('{')-stripped.count('}')
        opened=opened or '{' in stripped
        if opened and depth==0:return ''.join(result)
        if depth<0:return None
    return None

def main():
    inv=json.loads((ROOT/'reports/replica/batch-completeness-inventory.json').read_text())
    mapping=json.loads((ROOT/'replica/function-map.json').read_text())['functions']
    cache={};results=[];counts=Counter()
    for x in inv['rows']:
        if x['state']!='migrated' or x['source_binding']!='file_changed_needs_method_review':continue
        row=mapping[x['function_id']]; ev=json.loads((ROOT/row['migration_evidence']).read_text()); refs=[]
        for ref in row.get('implementations',[]):
            path,symbol=ref['path'],ref['symbol']; expected=ev.get('source_sha256',{}).get(path)
            if path not in cache:
                p=ROOT/path; current=p.read_bytes() if p.is_file() else b''
                git=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                cache[path]=(current,git.stdout if git.returncode==0 else b'')
            current,old=cache[path]
            if not expected:kind='missing_snapshot'
            elif hashlib.sha256(current).hexdigest()==expected:kind='unchanged_file'
            elif not old or hashlib.sha256(old).hexdigest()!=expected:kind='historical_snapshot_unavailable'
            else:
                a=body(old.decode('utf-8'),symbol);b=body(current.decode('utf-8'),symbol)
                if a is None or b is None:kind='ambiguous_symbol_or_syntax'
                elif a==b:kind='identical_method_candidate'
                else:kind='method_changed'
            refs.append({'path':path,'symbol':symbol,'classification':kind})
            counts[kind]+=1
        results.append({'function_id':x['function_id'],'references':refs})
    qualified=[x for x in results if any(y['classification']=='identical_method_candidate' for y in x['references'])]
    report={'policy':'仅筛选方法文本完全相同的待审候选；必须复核其他源码引用、调用者和原函数合同，绝不自动计为完整。','build_executed':False,'tests_executed':False,'records_examined':len(results),'reference_counts':dict(counts),'candidate_functions':len(qualified),'records':results}
    (ROOT/'reports/replica/batch-unchanged-method-candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))

if __name__=='__main__':main()
