// Offline tests: the proposed PR snapshot must never select its own policy.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const text = fs.readFileSync('.github/workflows/policy-governance-self.yml','utf8');
const script = text.split('      - id: policy-revision\n')[1].split('          script: |\n')[1].split('\n      - name: Check out pinned canonical policy source')[0].split('\n').map(x=>x.startsWith('            ')?x.slice(12):x).join('\n');
const run = async (event, overrides={}) => {
  const base='a'.repeat(40), proposed='b'.repeat(40);
  const context={eventName:event,ref:'refs/heads/main',sha:proposed,payload:{repository:{id:1461539726,full_name:'djconnect-music-dj/.github'},pull_request:{base:{sha:base,ref:'main',repo:{id:1461539726}}}}};
  if (overrides.badRepo) context.payload.repository.id=7;
  if (overrides.badBase) context.payload.pull_request.base.repo.id=7;
  if (overrides.stale) context.payload.pull_request.base.sha='c'.repeat(40);
  let output;
  const github={rest:{repos:{getBranch:async()=>({data:{commit:{sha:event==='push'?proposed:base}}})}}};
  await new (Object.getPrototypeOf(async function(){}).constructor)('context','github','core',script)(context,github,{setOutput:(_,v)=>{output=v}});
  return output;
};
test('PR that changes policy selects trusted base, never proposed commit',async()=>assert.equal(await run('pull_request'),'a'.repeat(40)));
test('main push selects exact push SHA',async()=>assert.equal(await run('push'),'b'.repeat(40)));
test('stale, foreign repository and unsupported event fail closed',async()=>{
  for (const opts of [{stale:true},{badRepo:true},{badBase:true}]) await assert.rejects(run('pull_request',opts));
  await assert.rejects(run('workflow_dispatch'));
});
