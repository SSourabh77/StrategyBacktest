from src.core.strategy_base import BaseStrategy
from src.strategies.bollinger_band_breakout import BollingerBandBreakoutStrategy
from src.strategies.calendar_spread import CalendarSpreadStrategy
from src.strategies.delta_neutral import DeltaNeutralStrategy
from src.strategies.ema_adx_crossover import EmaAdxCrossoverStrategy
from src.strategies.gamma_scalping import GammaScalpingStrategy
from src.strategies.iron_condor import IronCondorStrategy
from src.strategies.macd_crossover import MacdCrossoverStrategy
from src.strategies.machine_learning_signal_model import MachineLearningSignalStrategy
from src.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy
from src.strategies.option_greeks_based import OptionGreeksBasedStrategy
from src.strategies.price_action_breakout import PriceActionBreakoutStrategy
from src.strategies.rsi_mean_reversion import RsiMeanReversionStrategy
from src.strategies.sma_crossover import SmaCrossoverStrategy
from src.strategies.statistical_arbitrage import StatisticalArbitrageStrategy
from src.strategies.straddle_strangle import StraddleStrangleStrategy
from src.strategies.supertrend import SupertrendStrategy
from src.strategies.vwap_breakout import VwapBreakoutStrategy


STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    EmaAdxCrossoverStrategy.name: EmaAdxCrossoverStrategy,
    SmaCrossoverStrategy.name: SmaCrossoverStrategy,
    SupertrendStrategy.name: SupertrendStrategy,
    VwapBreakoutStrategy.name: VwapBreakoutStrategy,
    OpeningRangeBreakoutStrategy.name: OpeningRangeBreakoutStrategy,
    RsiMeanReversionStrategy.name: RsiMeanReversionStrategy,
    MacdCrossoverStrategy.name: MacdCrossoverStrategy,
    BollingerBandBreakoutStrategy.name: BollingerBandBreakoutStrategy,
    PriceActionBreakoutStrategy.name: PriceActionBreakoutStrategy,
    OptionGreeksBasedStrategy.name: OptionGreeksBasedStrategy,
    DeltaNeutralStrategy.name: DeltaNeutralStrategy,
    GammaScalpingStrategy.name: GammaScalpingStrategy,
    StraddleStrangleStrategy.name: StraddleStrangleStrategy,
    IronCondorStrategy.name: IronCondorStrategy,
    CalendarSpreadStrategy.name: CalendarSpreadStrategy,
    StatisticalArbitrageStrategy.name: StatisticalArbitrageStrategy,
    MachineLearningSignalStrategy.name: MachineLearningSignalStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    if name not in STRATEGY_REGISTRY:
        known = ", ".join(sorted(STRATEGY_REGISTRY))
        raise KeyError(f"Unknown strategy '{name}'. Known strategies: {known}")
    return STRATEGY_REGISTRY[name]()
