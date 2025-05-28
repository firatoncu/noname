import React, { useState, useEffect, memo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, TrendingUp, TrendingDown, LineChart, X, Target, AlertCircle, Clock } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

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
    };
    pricePrecision: number;
}

export const PositionCard: React.FC<PositionCardProps> = ({ position, pricePrecision }) => {
    const navigate = useNavigate();
    const { isDarkMode } = useTheme();
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
    // Use refs to track previous values to prevent unnecessary updates
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
        <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 mb-4 transition-colors duration-200`}>
            {/* Header with Symbol, Side, and Action Buttons */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                    <span className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        {position.symbol}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        isLong 
                            ? isDarkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
                            : isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800'
                    }`}>
                        {isLong ? 'LONG' : 'SHORT'}
                    </span>
                    <div className="flex items-center">
                        <DollarSign className={`w-5 h-5 ${isDarkMode ? 'text-blue-400' : 'text-blue-500'} mr-1`} />
                        <span className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                            ${Math.abs(parseFloat(position.notional)).toFixed(2)}
                        </span>
                    </div>
                    {/* Opened Time */}
                    <div className="flex items-center space-x-2 bg-opacity-10 px-3 py-1.5 rounded-md ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}">
                        <Clock className={`w-4 h-4 ${isDarkMode ? 'text-blue-400' : 'text-blue-500'}`} />
                        <div className="flex flex-col">
                            <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Opened</span>
                            <span className={`text-sm font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>
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
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setDialogState({ showTPSLDialog: true })}
                        className={`flex items-center space-x-1 px-3 py-1 rounded-md 
                            ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
                        title="Set TP/SL"
                    >
                        <Target size={16} />
                        <span>Set TP/SL</span>
                    </button>
                    <button
                        onClick={() => setDialogState({ showCloseConfirm: true })}
                        disabled={isClosing}
                        className={`flex items-center space-x-1 px-3 py-1 rounded-md 
                            ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white`}
                        title="Close Position"
                    >
                        <X size={16} />
                        <span>{isClosing ? 'Closing...' : 'Close Position'}</span>
                    </button>
                </div>
            </div>

            {error && (
                <div className={`mb-4 p-2 rounded-md ${isDarkMode ? 'bg-red-900/50 text-red-200' : 'bg-red-100 text-red-700'}`}>
                    {error}
                </div>
            )}

            {/* Position Details Grid */}
            <div className="grid grid-cols-3 gap-6 mb-6">
                {/* P&L Section */}
                <div className="flex flex-col">
                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>P&L</span>
                    <div className="flex items-center">
                        {isLong ? (
                            <TrendingUp className={`w-5 h-5 ${pnl >= 0 ? 'text-green-500' : 'text-red-500'} mr-1`} />
                        ) : (
                            <TrendingDown className={`w-5 h-5 ${pnl >= 0 ? 'text-green-500' : 'text-red-500'} mr-1`} />
                        )}
                        <span className={`font-semibold ${pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            ${pnl.toFixed(2)} ({pnlPercentage.toFixed(2)}%)
                        </span>
                    </div>
                </div>

                {/* Entry Price */}
                <div className="flex flex-col">
                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Entry Price</span>
                    <span className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                        ${parseFloat(position.entryPrice).toFixed(2)}
                    </span>
                </div>

                {/* Current Price */}
                <div className="flex flex-col">
                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Current Price</span>
                    <span className={`font-semibold ${isDarkMode ? 'text-purple-400' : 'text-purple-600'}`}>
                        ${parseFloat(position.markPrice).toFixed(2)}
                    </span>
                </div>


            </div>

            {/* Market TP/SL Section */}
            <div className="mb-6 p-4 rounded-lg bg-opacity-10 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}">
                <h4 className={`text-sm font-semibold mb-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Market Take Profit / Stop Loss
                </h4>
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col">
                        <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Take Profit</span>
                        <span className={`font-semibold ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>
                            ${hardtakeProfit}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Stop Loss</span>
                        <span className={`font-semibold ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                            ${hardstopLoss}
                        </span>
                    </div>
                </div>
            </div>

            {/* Custom TP/SL Section */}
            {(position.takeProfitPrice || position.stopLossPrice) && (
                <div className="mb-6 p-4 rounded-lg bg-opacity-10 ${isDarkMode ? 'bg-blue-900/20' : 'bg-blue-50'}">
                    <div className="flex items-center gap-2 mb-3">
                        <h4 className={`text-sm font-semibold ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                            Custom Take Profit / Stop Loss
                        </h4>
                        <button
                            onClick={() => handleCloseLimitOrders()}
                            disabled={getDialogState().isClosingLimit}
                            className={`flex items-center space-x-1 px-2 py-1 rounded-md text-xs
                                ${isDarkMode ? 'bg-red-900 hover:bg-red-800' : 'bg-red-800 hover:bg-red-700'} text-white`}
                            title="Cancel All Orders"
                        >
                            <X size={14} />
                            <span>{getDialogState().isClosingLimit ? 'Canceling...' : 'Cancel All'}</span>
                        </button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        {position.takeProfitPrice && (
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Take Profit</span>
                                    <button
                                        onClick={() => handleCloseLimitOrders('TP')}
                                        disabled={getDialogState().isClosingTP}
                                        className={`flex items-center space-x-1 px-1.5 py-0.5 rounded-md text-xs
                                            ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white`}
                                        title="Cancel Take Profit"
                                    >
                                        <X size={12} />
                                        <span>{getDialogState().isClosingTP ? 'Canceling...' : 'Cancel'}</span>
                                    </button>
                                </div>
                                <span className={`font-semibold ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>
                                    ${parseFloat(position.takeProfitPrice).toFixed(2)}
                                </span>
                            </div>
                        )}
                        {position.stopLossPrice && (
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Stop Loss</span>
                                    <button
                                        onClick={() => handleCloseLimitOrders('SL')}
                                        disabled={getDialogState().isClosingSL}
                                        className={`flex items-center space-x-1 px-1.5 py-0.5 rounded-md text-xs
                                            ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white`}
                                        title="Cancel Stop Loss"
                                    >
                                        <X size={12} />
                                        <span>{getDialogState().isClosingSL ? 'Canceling...' : 'Cancel'}</span>
                                    </button>
                                </div>
                                <span className={`font-semibold ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                                    ${parseFloat(position.stopLossPrice).toFixed(2)}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* View Chart Button */}
            <div className="flex justify-end">
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
                    className={`flex items-center space-x-1 px-3 py-1 rounded-md 
                        ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} text-white font-medium`}
                >
                    <LineChart className="w-4 h-4" />
                    <span>View Chart</span>
                </button>
            </div>

            {/* TP/SL Dialog */}
            {getDialogState().showTPSLDialog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-white'} w-96`}>
                        <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Set Take Profit / Stop Loss
                        </h3>
                        
                        <div className="space-y-4">
                            <div>
                                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Take Profit (%)
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().tpPercentage}
                                    onChange={(e) => setDialogState({ tpPercentage: e.target.value })}
                                    className={`mt-1 block w-full rounded-md ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2`}
                                    placeholder="Enter percentage"
                                />
                            </div>
                            
                            <div>
                                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Stop Loss (%)
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().slPercentage}
                                    onChange={(e) => setDialogState({ slPercentage: e.target.value })}
                                    className={`mt-1 block w-full rounded-md ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2`}
                                    placeholder="Enter percentage"
                                />
                            </div>

                            <div>
                                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Take Profit Price
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().tpPrice}
                                    onChange={(e) => setDialogState({ tpPrice: e.target.value })}
                                    className={`mt-1 block w-full rounded-md ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2`}
                                    placeholder="Enter price"
                                />
                            </div>
                            
                            <div>
                                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                    Stop Loss Price
                                </label>
                                <input
                                    type="number"
                                    value={getDialogState().slPrice}
                                    onChange={(e) => setDialogState({ slPrice: e.target.value })}
                                    className={`mt-1 block w-full rounded-md ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2`}
                                    placeholder="Enter price"
                                />
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end space-x-3">
                            <button
                                onClick={() => setDialogState({ showTPSLDialog: false })}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} text-sm font-medium`}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSetTPSL}
                                disabled={getDialogState().isSettingTPSL}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white text-sm font-medium`}
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
                    <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-white'} w-96`}>
                        <div className="flex items-center space-x-3 mb-4">
                            <AlertCircle className={`w-6 h-6 ${isDarkMode ? 'text-red-400' : 'text-red-500'}`} />
                            <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                Close Position
                            </h3>
                        </div>
                        <p className={`mb-6 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                            Are you sure you want to close your {position.symbol} {isLong ? 'LONG' : 'SHORT'} position?
                        </p>
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={() => setDialogState({ showCloseConfirm: false })}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} text-sm font-medium`}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleClosePosition}
                                disabled={isClosing}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white text-sm font-medium`}
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