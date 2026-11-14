import { fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

vi.mock('maplibre-gl', () => ({ Map: class { remove() {} } }))

import { App } from './App'
import { fixtures } from '../types/contracts'

beforeEach(() => window.history.replaceState({}, '', '/'))
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
describe('public-safe shell',()=>{
  it('filters the prototype source catalogue without claiming live freshness', async()=>{
    vi.stubGlobal('fetch', vi.fn(async () => ({ok:false,status:401,json:async()=>({error:{code:'UNAUTHENTICATED'}})})))
    window.history.replaceState({},'', '/sources')
    render(<App/>)
    expect(await screen.findByRole('heading',{name:'Sources and citations'})).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:'NASA'}))
    expect(within(screen.getByRole('table')).getByText('NISAR GCOV / GSLC')).toBeTruthy()
    expect(within(screen.getByRole('table')).queryByText('OpenStreetMap')).toBeNull()
    fireEvent.change(screen.getByLabelText('Filter datasets'),{target:{value:'FIRMS'}})
    expect(within(screen.getByRole('table')).getByText('FIRMS VIIRS')).toBeTruthy()
    const row=screen.getByRole('row',{name:/FIRMS VIIRS/})
    fireEvent.keyDown(row,{key:'Enter'})
    expect(row.getAttribute('aria-selected')).toBe('true')
  })

  it('shows restricted route and shelter views only to a coordinator', async()=>{
    vi.stubGlobal('fetch', vi.fn(async () => ({ok:true,json:async()=>({user_id:'coordinator',role:'coordinator',area_scopes:['demo-area-01'],csrf_token:'csrf',synthetic:true})})))
    window.history.replaceState({},'', '/routes')
    render(<App/>)
    expect(await screen.findByRole('heading',{name:'Routes'})).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:'Outbound'}))
    expect(screen.getByText('Outbound route options')).toBeTruthy()
    fireEvent.click(screen.getByRole('link',{name:'Shelters'}))
    expect(await screen.findByRole('heading',{name:'Shelter candidates'})).toBeTruthy()
  })
  it('labels synthetic content and never shows a shelter coordinate',async()=>{
    vi.stubGlobal('fetch', vi.fn(async () => ({ok:false,status:401,json:async()=>({error:{code:'UNAUTHENTICATED'}})})))
    render(<App/>)
    expect((await screen.findAllByText(/Illustrative demo data/i)).length).toBeGreaterThan(0)
    expect(await screen.findByText(/No approved public layers/)).toBeTruthy()
    expect(screen.queryByText(/Synthetic candidate A/)).toBeNull()
  })

  it('selects a synthetic area and displays API-backed evidence and source',async()=>{
    const fetchMock = vi.fn(async (url:string, options?:RequestInit) => {
      if (url.endsWith('/session') && options?.method !== 'POST') return {ok:false,status:401,json:async()=>({error:{code:'UNAUTHENTICATED'}})}
      if (url.endsWith('/session')) return {ok:true,json:async()=>({user_id:'analyst',role:'analyst',area_scopes:['demo-area-01'],csrf_token:'test-csrf',synthetic:true})}
      if (url.endsWith('/areas/demo-area-01/summary')) return {ok:true,json:async()=>fixtures.area}
      if (url.endsWith('/sources/demo-source-01')) return {ok:true,json:async()=>fixtures.source}
      throw new Error(`Unexpected URL: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App/>)
    expect(screen.queryByRole('button',{name:'Select synthetic demo area'})).toBeNull()
    fireEvent.click(await screen.findByRole('link',{name:'Sign in'}))
    fireEvent.change(screen.getByLabelText('Username'),{target:{value:'analyst'}})
    fireEvent.change(screen.getByLabelText('Password'),{target:{value:'local-test-password'}})
    fireEvent.click(screen.getByRole('button',{name:'Sign in'}))
    await screen.findByText('NISAR change workspace')
    fireEvent.click(screen.getByRole('button',{name:'Select synthetic demo area'}))
    expect(await screen.findByText('Synthetic NISAR contract fixture')).toBeTruthy()
    expect(screen.getByText(/Residents \(synthetic range\)/)).toBeTruthy()
    expect(within(screen.getByRole('region',{name:'Selected area summary'})).getByLabelText('Evidence: Unknown')).toBeTruthy()
    expect(screen.getByText(/Not performed for this fixture/)).toBeTruthy()
    expect(screen.getByText(/not evidence for the synthetic resident range/)).toBeTruthy()
    expect(fetchMock.mock.calls.map(([url])=>url)).toEqual(expect.arrayContaining([
      '/api/v1/areas/demo-area-01/summary','/api/v1/sources/demo-source-01']))
  })

  it('shows an unavailable state when the protected area request fails',async()=>{
    const fetchMock = vi.fn(async (url:string, options?:RequestInit) => {
      if (url.endsWith('/session') && options?.method !== 'POST') return {ok:false,status:401,json:async()=>({error:{code:'UNAUTHENTICATED'}})}
      if (url.endsWith('/session')) return {ok:true,json:async()=>({user_id:'analyst',role:'analyst',area_scopes:['demo-area-01'],csrf_token:'test-csrf',synthetic:true})}
      return {ok:false,json:async()=>({error:{code:'UNAVAILABLE',message:'No area',request_id:'test',details:[]},synthetic:true})}
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App/>)
    fireEvent.click(await screen.findByRole('link',{name:'Sign in'}))
    fireEvent.change(screen.getByLabelText('Username'),{target:{value:'analyst'}})
    fireEvent.change(screen.getByLabelText('Password'),{target:{value:'local-test-password'}})
    fireEvent.click(screen.getByRole('button',{name:'Sign in'}))
    fireEvent.click(await screen.findByRole('button',{name:'Select synthetic demo area'}))
    expect(await screen.findByText(/Area information is unavailable/)).toBeTruthy()
    expect(screen.queryByText('Synthetic NISAR contract fixture')).toBeNull()
  })

  it('restores a server session and clears protected content on expiry', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url:string) => url.endsWith('/session')
      ? {ok:true,json:async()=>({user_id:'analyst',role:'analyst',area_scopes:['demo-area-01'],csrf_token:'csrf',synthetic:true})}
      : {ok:false,status:401,json:async()=>({error:{code:'UNAUTHENTICATED'}})}))
    render(<App/>)
    expect(await screen.findByText('NISAR change workspace')).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:'Select synthetic demo area'}))
    expect(await screen.findByText(/Session expired/)).toBeTruthy()
    expect(screen.queryByText('NISAR change workspace')).toBeNull()
  })

  it('keeps the session on a scoped 403 and explains denial', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url:string) => url.endsWith('/session')
      ? {ok:true,json:async()=>({user_id:'analyst',role:'analyst',area_scopes:[],csrf_token:'csrf',synthetic:true})}
      : {ok:false,status:403,json:async()=>({error:{code:'FORBIDDEN'}})}))
    render(<App/>)
    fireEvent.click(await screen.findByRole('button',{name:'Select synthetic demo area'}))
    expect(await screen.findByText(/Access denied for this area/)).toBeTruthy()
    expect(screen.getByText('NISAR change workspace')).toBeTruthy()
  })

  it('opens prototype dock panels and filters empty alerts without inventing results', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ok:true,json:async()=>({user_id:'analyst',role:'analyst',area_scopes:['demo-area-01'],csrf_token:'csrf',synthetic:true})})))
    render(<App/>)
    fireEvent.click(await screen.findByRole('button',{name:/Damage.*Unavailable/i}))
    expect(screen.getByText(/No reviewed damage result is loaded/)).toBeTruthy()
    fireEvent.click(await screen.findByRole('button',{name:/Layers/}))
    expect(screen.getByRole('complementary',{name:'Layers'})).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:/Alerts/}))
    fireEvent.click(screen.getByRole('button',{name:'Radar'}))
    expect(screen.getByText(/No verified radar alerts loaded/)).toBeTruthy()
  })
})
