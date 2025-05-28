import React, { useState, useEffect, memo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, TrendingUp, TrendingDown, LineChart, X, Target, AlertCircle, Clock, Zap } from 'lucide-react';

interface PositionCardProps {
    position: {
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
    };
    pricePrecision: number;
}

export const PositionCard: React.FC<PositionCardProps> = ({ position, pricePrecision }) => {
    const navigate = useNavigate();
    const [isClosing, setIsClosing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Use refs to persist dialog state across re-renders
    const dialogStateRef = useRef({
        showTPSLDialog: false,
        showCloseConfirm: false,
        tpPercentage: '',
        slPercentage: '',
        tpPrice: '',
        slPrice: '',
        isSettingTPSL: false,
        isClosingLimit: false,
        isClosingTP: false,
        isClosingSL: false,
    });
    
    // Force re-render when dialog state changes
    const [, forceUpdate] = useState({});
    const triggerUpdate = useCallback(() => {
        forceUpdate({});
    }, []);
    
    // Getter and setter for dialog state
    const getDialogState = useCallback(() => dialogStateRef.current, []);
    const setDialogState = useCallback((updates: Partial<typeof dialogStateRef.current>) => {
        dialogStateRef.current = { ...dialogStateRef.current, ...updates };
        triggerUpdate();
    }, [triggerUpdate]);

    const handleClosePosition = async () => {
        try {
            setIsClosing(true);
            setError(null);
            const response = await fetch(`/api/close-position/${position.symbol}`, {
                method: 'POST',
            });
            const data = await response.json();
            if (data.error) {
                setError(data.error);
            }
            setDialogState({ showCloseConfirm: false });
        } catch (error) {
            console.error('Error closing position:', error);
            setError(error instanceof Error ? error.message : 'Failed to close position');
        } finally {
            setIsClosing(false);
        }
    };

    const handleSetTPSL = async () => {
        try {
            setDialogState({ isSettingTPSL: true });
            setError(null);
            
            const requestBody: any = {};
            const entryPrice = parseFloat(position.entryPrice);
            const isLong = parseFloat(position.positionAmt) > 0;

            if (getDialogState().tpPercentage) {
                const percentage = parseFloat(getDialogState().tpPercentage);
                const tpPrice = isLong 
                    ? entryPrice * (1 + percentage/100)
                    : entryPrice * (1 - percentage/100);
                requestBody.take_profit_price = Number(tpPrice.toFixed(pricePrecision));
            } else if (getDialogState().tpPrice) {
                requestBody.take_profit_price = Number(parseFloat(getDialogState().tpPrice).toFixed(pricePrecision));
            }

            if (getDialogState().slPercentage) {
                const percentage = parseFloat(getDialogState().slPercentage);
                const slPrice = isLong 
                    ? entryPrice * (1 - percentage/100)
                    : entryPrice * (1 + percentage/100);
                requestBody.stop_loss_price = Number(slPrice.toFixed(pricePrecision));
            } else if (getDialogState().slPrice) {
                requestBody.stop_loss_price = Number(parseFloat(getDialogState().slPrice).toFixed(pricePrecision));
            }

            const response = await fetch(`/api/set-tpsl/${position.symbol}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });
            
            const data = await response.json();
            if (data.error) {
                setError(data.error);
            } else {
                setDialogState({ showTPSLDialog: false, tpPercentage: '', slPercentage: '', tpPrice: '', slPrice: '' });
            }
        } catch (error) {
            console.error('Error setting TP/SL:', error);
            setError(error instanceof Error ? error.message : 'Failed to set TP/SL');
        } finally {
            setDialogState({ isSettingTPSL: false });
        }
    };

    const handleCloseLimitOrders = async (orderType?: 'TP' | 'SL') => {
        try {
            if (orderType === 'TP') {
                setDialogState({ isClosingTP: true });
            } else if (orderType === 'SL') {
                setDialogState({ isClosingSL: true });
            } else {
                setDialogState({ isClosingLimit: true });
            }
            setError(null);
            
            const response = await fetch(`/api/close-limit-orders/${position.symbol}${orderType ? `?order_type=${orderType}` : ''}`, {
                method: 'POST',
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to close limit orders');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            if (orderType === 'TP') {
                setDialogState({ isClosingTP: false });
            } else if (orderType === 'SL') {
                setDialogState({ isClosingSL: false });
            } else {
                setDialogState({ isClosingLimit: false });
            }
        }
    };

    const positionAmount = parseFloat(position.positionAmt);
    const isLong = positionAmount > 0;
    const pnl = parseFloat(position.unRealizedProfit);
    const pnlPercentage = (pnl / Math.abs(parseFloat(position.notional))) * 100;
    const entryPrice = parseFloat(position.entryPrice);
    const hardtakeProfit = isLong 
    ? (entryPrice * 1.0033).toFixed(pricePrecision)
    : (entryPrice * 0.9966).toFixed(pricePrecision);
    
    const hardstopLoss = isLong
    ? (entryPrice * 0.993).toFixed(pricePrecision)
    : (entryPrice * 1.007).toFixed(pricePrecision);
    
    // Add useEffect to pre-fill TP/SL values when dialog opens
    const prevDialogOpenRef = useRef(false);
    const prevTpPriceRef = useRef(position.takeProfitPrice);
    const prevSlPriceRef = useRef(position.stopLossPrice);
    
    useEffect(() => {
        const dialogOpen = getDialogState().showTPSLDialog;
        const tpPriceChanged = position.takeProfitPrice !== prevTpPriceRef.current;
        const slPriceChanged = position.stopLossPrice !== prevSlPriceRef.current;
        
        // Only update when dialog first opens or when TP/SL prices actually change
        if ((dialogOpen && !prevDialogOpenRef.current) || (dialogOpen && (tpPriceChanged || slPriceChanged))) {
            if (position.takeProfitPrice && tpPriceChanged) {
                setDialogState({ tpPrice: position.takeProfitPrice });
                // Calculate percentage based on entry price
                const tpPrice = parseFloat(position.takeProfitPrice);
                const tpPercentage = ((tpPrice - entryPrice) / entryPrice) * 100;
                setDialogState({ tpPercentage: tpPercentage.toFixed(2) });
            }
            if (position.stopLossPrice && slPriceChanged) {
                setDialogState({ slPrice: position.stopLossPrice });
                // Calculate percentage based on entry price
                const slPrice = parseFloat(position.stopLossPrice);
                const slPercentage = ((slPrice - entryPrice) / entryPrice) * 100;
                setDialogState({ slPercentage: slPercentage.toFixed(2) });
            }
        }
        
        // Update refs
        prevDialogOpenRef.current = dialogOpen;
        prevTpPriceRef.current = position.takeProfitPrice;
        prevSlPriceRef.current = position.stopLossPrice;
    }, [getDialogState().showTPSLDialog, position.takeProfitPrice, position.stopLossPrice, entryPrice, setDialogState]);

    return (
        <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 overflow-hidden group animate-scale-in">
            {/* Header Section */}
            <div className="bg-dark-bg-tertiary/50 px-6 py-4 border-b border-dark-border-secondary">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        {/* Symbol and Side */}
                        <div className="flex items-center space-x-3">
                            <h3 className="text-2xl font-bold text-dark-text-primary">
                                {position.symbol}
                            </h3>
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold transition-colors duration-300 ${
                                isLong 
                                    ? 'bg-dark-accent-success/20 text-dark-accent-success border border-dark-accent-success/30'
                                    : 'bg-dark-accent-error/20 text-dark-accent-error border border-dark-accent-error/30'
                            }`}>
                                {isLong ? 'LONG' : 'SHORT'}
                            </span>
                        </div>
                        
                        {/* Leverage Badge */}
                        <div className="flex items-center space-x-1 bg-dark-accent-primary/20 px-3 py-1 rounded-full border border-dark-accent-primary/30">
                            <Zap className="w-4 h-4 text-dark-accent-primary" />
                            <span className="text-sm font-semibold text-dark-accent-primary">
                                {position.leverage || 1}x
                            </span>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => setDialogState({ showTPSLDialog: true })}
                            className="flex items-center space-x-2 px-4 py-2 bg-dark-accent-primary hover:bg-dark-accent-secondary text-dark-text-primary rounded-xl transition-all duration-300 shadow-glow-sm hover:shadow-glow-md"
                            title="Set TP/SL"
                        >
                            <Target size={16} />
                            <span>TP/SL</span>
                        </button>
                        <button
                            onClick={() => navigate(`/position/current/${position.symbol}`, { 
                                state: { 
                                    position: {
                                        ...position,
                                        side: parseFloat(position.positionAmt) > 0 ? 'LONG' : 'SHORT',
                                        isActive: true,
                                        profit: position.unRealizedProfit,
                                        currentPrice: position.markPrice
                                    }
                                }
                            })}
                            className="flex items-center space-x-2 px-4 py-2 bg-dark-bg-hover hover:bg-dark-accent-info/20 text-dark-text-secondary hover:text-dark-accent-info border border-dark-border-secondary hover:border-dark-accent-info rounded-xl transition-all duration-300"
                        >
                            <LineChart size={16} />
                            <span>Chart</span>
                        </button>
                        <button
                            onClick={() => setDialogState({ showCloseConfirm: true })}
                            disabled={isClosing}
                            className="flex items-center space-x-2 px-4 py-2 bg-dark-accent-error hover:bg-dark-accent-error/80 text-dark-text-primary rounded-xl transition-all duration-300 disabled:opacity-50 shadow-glow-sm hover:shadow-glow-md"
                            title="Close Position"
                        >
                            <X size={16} />
                            <span>{isClosing ? 'Closing...' : 'Close'}</span>
                        </button>
                    </div>
                </div>
            </div>

            {error && (
                <div className="mx-6 mt-4 p-4 rounded-xl bg-dark-accent-error/10 text-dark-accent-error border border-dark-accent-error/30 backdrop-blur-sm animate-fade-in">
                    <div className="flex items-center space-x-2">
                        <AlertCircle size={16} />
                        <span>{error}</span>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="p-6 space-y-6">
                {/* P&L and Performance Section */}
                <div className="p-4 rounded-xl bg-dark-bg-tertiary/50 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                    <h4 className="text-sm font-semibold mb-4 text-dark-text-muted uppercase tracking-wide">
                        Performance
                    </h4>
                    <div className="grid grid-cols-2 gap-6">
                        {/* Regular P&L */}
                        <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                                {isLong ? (
                                    <TrendingUp className={`w-5 h-5 ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`} />
                                ) : (
                                    <TrendingDown className={`w-5 h-5 ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`} />
                                )}
                                <span className="text-sm text-dark-text-muted">Unrealized P&L</span>
                            </div>
                            <div className={`text-2xl font-bold ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                                ${pnl.toFixed(2)}
                            </div>
                            <div className={`text-sm ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                                {pnlPercentage >= 0 ? '+' : ''}{pnlPercentage.toFixed(2)}%
                            </div>
                        </div>

                        {/* Leveraged P&L */}
                        <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                                <Zap className={`w-5 h-5 ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`} />
                                <span className="text-sm text-dark-text-muted">Leveraged P&L</span>
                            </div>
                            <div className={`text-2xl font-bold ${pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                                ${(pnl * (position.leverage || 1)).toFixed(2)}
                            </div>
                            <div className="text-sm text-dark-text-disabled">
                                {((pnl * (position.leverage || 1)) / Math.abs(parseFloat(position.notional)) * 100).toFixed(2)}% of notional
                            </div>
                        </div>
                    </div>
                </div>

                {/* Position Details Section */}
                <div className="p-4 rounded-xl bg-dark-bg-tertiary/50 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                    <h4 className="text-sm font-semibold mb-4 text-dark-text-muted uppercase tracking-wide">
                        Position Details
                    </h4>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Entry Price */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Entry Price</span>
                            <div className="text-lg font-semibold text-dark-text-primary">
                                ${parseFloat(position.entryPrice).toFixed(2)}
                            </div>
                        </div>

                        {/* Current Price */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Current Price</span>
                            <div className="text-lg font-semibold text-dark-accent-secondary">
                                ${parseFloat(position.markPrice).toFixed(2)}
                            </div>
                        </div>

                        {/* Position Size */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Position Size</span>
                            <div className="text-lg font-semibold text-dark-text-primary">
                                {Math.abs(parseFloat(position.positionAmt)).toFixed(6)}
                            </div>
                        </div>

                        {/* Margin Used */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Margin Used</span>
                            <div className="text-lg font-semibold text-dark-accent-warning">
                                ${(Math.abs(parseFloat(position.notional)) / (position.leverage || 1)).toFixed(2)}
                            </div>
                        </div>
                    </div>

                    {/* Additional Info Row */}
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-dark-border-secondary">
                        {/* Notional Value */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Notional Value</span>
                            <div className="flex items-center space-x-2">
                                <DollarSign className="w-4 h-4 text-dark-accent-info" />
                                <span className="text-lg font-semibold text-dark-text-primary">
                                    ${Math.abs(parseFloat(position.notional)).toFixed(2)}
                                </span>
                            </div>
                        </div>

                        {/* Opened Time */}
                        <div className="space-y-2">
                            <span className="text-sm text-dark-text-muted">Opened</span>
                            <div className="flex items-center space-x-2">
                                <Clock className="w-4 h-4 text-dark-accent-info" />
                                <span className="text-lg font-semibold text-dark-text-primary">
                                    {new Date(position.entryTime).toLocaleString(undefined, {
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Take Profit / Stop Loss Section */}
                <div className="space-y-4">
                    {/* Market TP/SL */}
                    <div className="p-4 rounded-xl bg-dark-bg-tertiary/50 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                        <h4 className="text-sm font-semibold mb-4 text-dark-text-muted uppercase tracking-wide">
                            Market TP/SL (Default)
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <span className="text-sm text-dark-text-muted">Take Profit</span>
                                <div className="text-lg font-semibold text-dark-text-primary">
                                    ${hardtakeProfit}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <span className="text-sm text-dark-text-muted">Stop Loss</span>
                                <div className="text-lg font-semibold text-dark-text-primary">
                                    ${hardstopLoss}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Custom TP/SL */}
                    {(position.takeProfitPrice || position.stopLossPrice) && (
                        <div className="p-4 rounded-xl border-2 border-dark-border-accent bg-dark-bg-tertiary/50">
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="text-sm font-semibold text-dark-text-muted uppercase tracking-wide">
                                    Active TP/SL Orders
                                </h4>
                                <button
                                    onClick={() => handleCloseLimitOrders()}
                                    disabled={getDialogState().isClosingLimit}
                                    className="flex items-center space-x-1 px-3 py-1 bg-dark-accent-error hover:bg-dark-accent-error/80 text-dark-text-primary rounded-md text-xs transition-colors duration-300"
                                    title="Cancel All Orders"
                                >
                                    <X size={14} />
                                    <span>{getDialogState().isClosingLimit ? 'Canceling...' : 'Cancel All'}</span>
                                </button>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                {position.takeProfitPrice && (
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-dark-text-muted">Take Profit</span>
                                            <button
                                                onClick={() => handleCloseLimitOrders('TP')}
                                                disabled={getDialogState().isClosingTP}
                                                className="flex items-center space-x-1 px-2 py-1 bg-dark-accent-error hover:bg-dark-accent-error/80 text-dark-text-primary rounded text-xs"
                                                title="Cancel Take Profit"
                                            >
                                                <X size={10} />
                                                <span>{getDialogState().isClosingTP ? 'Canceling...' : 'Cancel'}</span>
                                            </button>
                                        </div>
                                        <div className="text-lg font-semibold text-dark-text-primary">
                                            ${parseFloat(position.takeProfitPrice).toFixed(2)}
                                        </div>
                                    </div>
                                )}
                                {position.stopLossPrice && (
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-dark-text-muted">Stop Loss</span>
                                            <button
                                                onClick={() => handleCloseLimitOrders('SL')}
                                                disabled={getDialogState().isClosingSL}
                                                className="flex items-center space-x-1 px-2 py-1 bg-dark-accent-error hover:bg-dark-accent-error/80 text-dark-text-primary rounded text-xs"
                                                title="Cancel Stop Loss"
                                            >
                                                <X size={10} />
                                                <span>{getDialogState().isClosingSL ? 'Canceling...' : 'Cancel'}</span>
                                            </button>
                                        </div>
                                        <div className="text-lg font-semibold text-dark-text-primary">
                                            ${parseFloat(position.stopLossPrice).toFixed(2)}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* TP/SL Dialog */}
            {getDialogState().showTPSLDialog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className={`p-6 rounded-lg bg-dark-bg-secondary w-96`}>
                        <h3 className={`text-lg font-semibold mb-4 text-dark-text-primary`}>
                            Set Take Profit / Stop Loss
                        </h3>
                        
                        <div className="space-y-4">
                            <div>
                                <label className={`block text-sm font-medium text-dark-text-muted`}>
                                    Take Profit (%)
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().tpPercentage}
                                    onChange={(e) => setDialogState({ tpPercentage: e.target.value })}
                                    className={`mt-1 block w-full rounded-md bg-dark-bg-tertiary text-dark-text-primary px-3 py-2`}
                                    placeholder="Enter percentage"
                                />
                            </div>
                            
                            <div>
                                <label className={`block text-sm font-medium text-dark-text-muted`}>
                                    Stop Loss (%)
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().slPercentage}
                                    onChange={(e) => setDialogState({ slPercentage: e.target.value })}
                                    className={`mt-1 block w-full rounded-md bg-dark-bg-tertiary text-dark-text-primary px-3 py-2`}
                                    placeholder="Enter percentage"
                                />
                            </div>

                            <div>
                                <label className={`block text-sm font-medium text-dark-text-muted`}>
                                    Take Profit Price
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().tpPrice}
                                    onChange={(e) => setDialogState({ tpPrice: e.target.value })}
                                    className={`mt-1 block w-full rounded-md bg-dark-bg-tertiary text-dark-text-primary px-3 py-2`}
                                    placeholder="Enter price"
                                />
                            </div>
                            
                            <div>
                                <label className={`block text-sm font-medium text-dark-text-muted`}>
                                    Stop Loss Price
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().slPrice}
                                    onChange={(e) => setDialogState({ slPrice: e.target.value })}
                                    className={`mt-1 block w-full rounded-md bg-dark-bg-tertiary text-dark-text-primary px-3 py-2`}
                                    placeholder="Enter price"
                                />
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end space-x-3">
                            <button
                                onClick={() => setDialogState({ showTPSLDialog: false })}
                                className={`px-4 py-2 rounded-md bg-dark-bg-tertiary text-dark-text-primary`}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSetTPSL}
                                disabled={getDialogState().isSettingTPSL}
                                className={`px-4 py-2 rounded-md bg-dark-accent-primary text-dark-text-primary`}
                            >
                                {getDialogState().isSettingTPSL ? 'Setting...' : 'Set TP/SL'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Close Position Confirmation Dialog */}
            {getDialogState().showCloseConfirm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className={`p-6 rounded-lg bg-dark-bg-secondary w-96`}>
                        <div className="flex items-center space-x-3 mb-4">
                            <AlertCircle className={`w-6 h-6 text-dark-accent-error`} />
                            <h3 className={`text-lg font-semibold text-dark-text-primary`}>
                                Close Position
                            </h3>
                        </div>
                        <p className={`mb-6 text-dark-text-muted`}>
                            Are you sure you want to close your {position.symbol} {isLong ? 'LONG' : 'SHORT'} position?
                        </p>
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={() => setDialogState({ showCloseConfirm: false })}
                                className={`px-4 py-2 rounded-md bg-dark-bg-tertiary text-dark-text-primary`}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleClosePosition}
                                disabled={isClosing}
                                className={`px-4 py-2 rounded-md bg-dark-accent-error text-dark-text-primary`}
                            >
                                {isClosing ? 'Closing...' : 'Close Position'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Custom comparison function to prevent unnecessary re-renders
const areEqual = (prevProps: PositionCardProps, nextProps: PositionCardProps) => {
    // Only re-render if critical position data has changed
    const prev = prevProps.position;
    const next = nextProps.position;
    
    // Helper function to compare numbers with tolerance
    const numbersEqual = (a: string | undefined, b: string | undefined, tolerance = 0.001) => {
        if (a === b) return true;
        if (!a || !b) return a === b;
        const numA = parseFloat(a);
        const numB = parseFloat(b);
        if (isNaN(numA) || isNaN(numB)) return a === b;
        return Math.abs(numA - numB) < tolerance;
    };
    
    // More aggressive tolerance for smoother updates
    const isEqual = (
        prev.symbol === next.symbol &&
        prev.positionAmt === next.positionAmt &&
        numbersEqual(prev.unRealizedProfit, next.unRealizedProfit, 0.05) && // Increased tolerance
        numbersEqual(prev.markPrice, next.markPrice, 0.05) && // Increased tolerance
        prev.takeProfitPrice === next.takeProfitPrice &&
        prev.stopLossPrice === next.stopLossPrice &&
        prev.entryPrice === next.entryPrice && // Add entry price check
        prev.entryTime === next.entryTime && // Add entry time check
        prevProps.pricePrecision === nextProps.pricePrecision
    );
    
    return isEqual;
};

// Export memoized component
export default memo(PositionCard, areEqual);