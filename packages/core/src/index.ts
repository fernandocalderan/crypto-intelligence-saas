export type Asset = {
  symbol: string;
  name: string;
  category: string;
  priceUsd: number;
  change24h: number;
  volume24h: number;
  momentumScore: number;
};

export type Signal = {
  id: string;
  assetSymbol: string;
  signalType: string;
  timeframe: string;
  confidence: number;
  score: number;
  thesis: string;
  generatedAt: string;
};

export type UserPlan = "starter" | "pro" | "desk";

