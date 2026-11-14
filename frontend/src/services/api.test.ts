import { afterEach, expect, it, vi } from 'vitest'
import { request } from './api'
afterEach(()=>vi.unstubAllGlobals())
it('turns server denials into typed errors, never fixture success',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({error:{code:'FORBIDDEN',message:'Denied',request_id:'demo',details:[]},synthetic:true})}))
  await expect(request('/shelters')).rejects.toMatchObject({error:{code:'FORBIDDEN'}})
})
