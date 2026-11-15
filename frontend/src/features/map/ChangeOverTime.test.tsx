import { readFileSync } from 'node:fs'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { MapData } from '../../types/map'
import { ChangeOverTime } from './ChangeOverTime'

const data = JSON.parse(readFileSync('public/sample/civisar-3d-sample.json', 'utf-8')) as MapData
afterEach(cleanup)

it('asks for an area and lists incidents when none is selected', () => {
  const onPick = vi.fn()
  render(<ChangeOverTime data={data} incident={null} sample onPick={onPick} onClose={() => {}} />)
  expect(screen.getByText('Pick an area')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: data.incidents[0].name }))
  expect(onPick).toHaveBeenCalledWith(data.incidents[0].id)
})

it('shows the series for the selected incident and steps with the slider and polarization switch', () => {
  const inc = data.incidents.find(i => i.id === 'inc-khiam')!
  const { container } = render(<ChangeOverTime data={data} incident={inc} sample onPick={() => {}} onClose={() => {}} />)
  expect(screen.getAllByText(/Sample data/).length).toBeGreaterThan(0)
  expect(screen.getByText('Corroborated')).toBeTruthy()
  expect(screen.getByText(/War period/)).toBeTruthy()
  const slider = screen.getByRole('slider', { name: 'Satellite pass' }) as HTMLInputElement
  expect(slider.max).toBe('16')
  fireEvent.change(slider, { target: { value: '0' } })
  expect(screen.getByText('Pre-war baseline: seasonal change or noise')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'HV' }))
  expect(screen.getByRole('button', { name: 'HV' }).getAttribute('aria-pressed')).toBe('true')
  expect(container.textContent ?? '').not.toMatch(/confirmed|\bsafe\b|live detection/i)
})
