export type SignalDefinition = {
  key: string;
  label: string;
  timeframe: "15m" | "1h" | "4h" | "1d";
  description: string;
  scoreWeights: {
    priceStructure: number;
    volume: number;
    derivatives: number;
    marketBreadth: number;
  };
};

export const MVP_SIGNAL_CATALOG: SignalDefinition[] = [
  {
    key: "momentum-breakout",
    label: "Momentum Breakout",
    timeframe: "4h",
    description: "Detecta rupturas con expansión de volumen y confirmación de estructura.",
    scoreWeights: {
      priceStructure: 0.4,
      volume: 0.3,
      derivatives: 0.2,
      marketBreadth: 0.1
    }
  },
  {
    key: "relative-strength",
    label: "Relative Strength",
    timeframe: "1d",
    description: "Mide liderazgo relativo del activo frente a majors y mercado amplio.",
    scoreWeights: {
      priceStructure: 0.35,
      volume: 0.15,
      derivatives: 0.15,
      marketBreadth: 0.35
    }
  },
  {
    key: "capital-rotation",
    label: "Capital Rotation",
    timeframe: "1d",
    description: "Evalúa rotación de flujo entre BTC, ETH y altcoins con sesgo direccional.",
    scoreWeights: {
      priceStructure: 0.25,
      volume: 0.25,
      derivatives: 0.2,
      marketBreadth: 0.3
    }
  }
];

