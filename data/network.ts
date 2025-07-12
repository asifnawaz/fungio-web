import { IconType } from 'react-icons';

export interface Node {
  id: number;
  name: string;
  coordinates: [number, number];
}

export interface Arc {
  from: number;
  to: number;
}

export const nodes: Node[] = [
  { id: 0, name: 'N. America', coordinates: [-100.0, 40.0] },
  { id: 1, name: 'S. America', coordinates: [-60.0, -20.0] },
  { id: 2, name: 'Europe', coordinates: [15.0, 50.0] },
  { id: 3, name: 'Africa', coordinates: [20.0, 10.0] },
  { id: 4, name: 'Asia', coordinates: [90.0, 40.0] },
  { id: 5, name: 'Oceania', coordinates: [135.0, -25.0] },
];

export const arcs: Arc[] = [
  { from: 0, to: 2 },
  { from: 1, to: 2 },
  { from: 2, to: 4 },
  { from: 3, to: 4 },
  { from: 4, to: 5 },
  { from: 0, to: 4 },
  { from: 1, to: 5 },
];
