export type SetStatus = 'collecting' | 'complete' | 'wanted' | 'dismantled';
export type Condition = 'new' | 'used';

export interface Paged<T> {
  page: number;
  pageSize: number;
  sortKey: string;
  sortDirection: 'ascending' | 'descending';
  totalRecords: number;
  records: T[];
}

export interface SetSummary {
  id: number;
  setNumber: string;
  name: string;
  status: SetStatus;
  imageUrl?: string;
  thumbnailUrl?: string;
  stats?: { owned: number; missing: number; pricePerPiece?: number };
}

export interface SetDetail {
  id: number;
  itemType: 'SET';
  setNumber: string;
  name: string;
  status: SetStatus;
  condition?: Condition;
  copies: number;
  storageLocation?: string;
  theme?: string;
  subtheme?: string;
  year?: number;
  pieces?: number;
  minifigs?: number;
  rrp?: number;
  acquiredPrice?: number;
  acquiredDate?: string;
  launchDate?: string;
  exitDate?: string | null;
  imageUrl?: string;
  stats: { owned: number; missing: number; pricePerPiece?: number };
  currentValue: number | null;
  gainLoss: number | null;
  links: { bricklink?: string };
}

export interface SetPartRow {
  setPartId: number;
  partNo: string;
  name: string;
  colorId: number;
  colorName: string;
  thumbnailUrl?: string;
  quantity: number;
  extraQuantity: number;
  owned: number;
  missing: number;
  isAlternate: boolean;
  isCounterpart: boolean;
  matchNo: number;
}

export interface InstructionRow {
  id: number;
  description: string;
  sourceUrl: string;
  downloaded: boolean;
  localPath?: string | null;
  sizeBytes?: number | null;
}

export interface QueueItem {
  id: string;
  name: string;
  status: string;
  progressBytes?: number;
  totalBytes?: number;
  startedAt?: string;
}

export interface HistoryItem {
  id: number;
  eventType: string;
  name: string;
  completedAt: string;
  status: string;
}

export interface SystemStatus {
  version: string;
  database: { connected: boolean };
  dataSources: {
    bricklink: { reachable: boolean; budgetRemaining?: number; budgetCap?: number };
    brickset: { reachable: boolean };
  };
}

export interface SystemTask {
  name: string;
  interval: string;
  lastRun?: string;
  nextRun?: string;
  lastDuration?: string;
}

export interface ApiKey {
  id: number;
  name: string;
  keyPrefix: string;
  key?: string;
  lastUsedAt?: string | null;
  createdAt: string;
}

export interface AuthLoginResponse {
  user: string;
}

export type AuthMode = 'forms' | 'disabled-for-local' | 'external';

export interface ValidationError {
  propertyName: string;
  errorMessage: string;
}
