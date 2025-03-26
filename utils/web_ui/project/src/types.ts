export interface Position {
  symbol: string;
  positionAmt: string;
  notional: string;
  unRealizedProfit: string;
  entryPrice: string;
  markPrice: string;
}

export interface TradingConditions {
  symbol: string;
  fundingPeriod: boolean;
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