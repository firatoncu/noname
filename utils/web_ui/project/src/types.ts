export interface Position {
  symbol: string;
  positionAmt: string;
  notional: string;
  unRealizedProfit: string;
  entryPrice: string;
  markPrice: string;
  entryTime: string;
  takeProfitPrice?: string;
  stopLossPrice?: string;
  leverage?: number;
}

export interface HistoricalPosition {
  symbol: string;
  entryPrice: string;
  exitPrice: string;
  profit: string;
  amount: string;
  side: 'LONG' | 'SHORT';
  openedAt: string;
  closedAt: string;
}

export interface WalletInfo {
  totalBalance: string;
  availableBalance: string;
  unrealizedPnL: string;
  dailyPnL: string;
  weeklyPnL: string;
  marginRatio: string;
}

export interface TradingConditions {
  symbol: string;
  strategyName: string;
  fundingPeriod: boolean;
  trendingCondition: boolean;
  buyConditions: {
    condA: boolean;
    condB: boolean;
    condC: boolean;
  };
  sellConditions: {
    condA: boolean;
    condB: boolean;
    condC: boolean;
  };
}