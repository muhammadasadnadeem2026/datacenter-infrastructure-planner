import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { CapacityTable } from '../components/results/CapacityTable';
import { MetricCard } from '../components/results/MetricCard';
import { WarningsPanel } from '../components/results/WarningsPanel';
import type { CapacityRow, Step } from '../types/api';

const step: Step = {
  key: 'it_kva',
  label: 'Apparent power',
  value: 63.1578947368,
  unit: 'kVA',
  formula: 'kVA = kW / PF',
  substitution: '60 / 0.95',
  assumption: '',
  reference: '',
};

describe('MetricCard', () => {
  it('shows the engine value and reveals the derivation', () => {
    render(
      <MemoryRouter>
        <MetricCard label="Apparent Power" step={step} />
      </MemoryRouter>,
    );
    expect(screen.getByText('63.16')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Show calculation'));
    expect(screen.getByText('kVA = kW / PF')).toBeInTheDocument();
    expect(screen.getByText(/60 \/ 0.95/)).toBeInTheDocument();
  });
});

describe('WarningsPanel', () => {
  it('renders a severity label, not colour alone', () => {
    render(
      <MemoryRouter>
        <WarningsPanel
          warnings={[
            {
              severity: 'critical',
              code: 'X',
              title: 'Transformer capacity exceeded',
              message: 'm',
              affected_system: 'transformer',
              reference: '',
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Transformer capacity exceeded')).toBeInTheDocument();
  });
  it('states when there are no warnings', () => {
    render(<WarningsPanel warnings={[]} />);
    expect(screen.getByText(/No engineering warnings/)).toBeInTheDocument();
  });
});

describe('CapacityTable', () => {
  it('highlights the bottleneck', () => {
    const row: CapacityRow = {
      system: 'transformer',
      label: 'Transformer',
      required: 8842,
      installed: 9000,
      usable: 9000,
      unit: 'kVA',
      redundancy: 'N',
      loading_pct: 98.2,
      reserve: 158,
      max_it_kw: 8550,
      usable_kw_equivalent: 8550,
      status: 'caution',
      note: '',
    };
    render(
      <CapacityTable
        rows={[row]}
        bottleneck={{
          system: 'transformer',
          label: 'Transformer',
          loading_pct: 98.2,
          max_it_kw: 8550,
          status: 'caution',
          message: 'Transformer is the limiting system.',
        }}
      />,
    );
    expect(screen.getByText(/System bottleneck: Transformer/)).toBeInTheDocument();
    expect(screen.getByText('98.2 %')).toBeInTheDocument();
  });
});
