import React, { useState, useEffect } from 'react';
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
    const [showTPSLDialog, setShowTPSLDialog] = useState(false);
    const [showCloseConfirm, setShowCloseConfirm] = useState(false);
    const [tpPercentage, setTpPercentage] = useState('');
    const [slPercentage, setSlPercentage] = useState('');
    const [tpPrice, setTpPrice] = useState('');
    const [slPrice, setSlPrice] = useState('');
    const [isSettingTPSL, setIsSettingTPSL] = useState(false);
    const [limitTPSL, setLimitTPSL] = useState<{tp?: number, sl?: number}>({});
    const [isClosingLimit, setIsClosingLimit] = useState(false);
    const [isClosingTP, setIsClosingTP] = useState(false);
    const [isClosingSL, setIsClosingSL] = useState(false);
    



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
            setShowCloseConfirm(false);
        } catch (error) {
            console.error('Error closing position:', error);
            setError(error instanceof Error ? error.message : 'Failed to close position');
        } finally {
            setIsClosing(false);
        }
    };

    const handleSetTPSL = async () => {
        try {
            setIsSettingTPSL(true);
            setError(null);
            
            const requestBody: any = {};
            const entryPrice = parseFloat(position.entryPrice);
            const isLong = parseFloat(position.positionAmt) > 0;

            if (tpPercentage) {
                const percentage = parseFloat(tpPercentage);
                const tpPrice = isLong 
                    ? entryPrice * (1 + percentage/100)
                    : entryPrice * (1 - percentage/100);
                requestBody.take_profit_price = Number(tpPrice.toFixed(pricePrecision));
            } else if (tpPrice) {
                requestBody.take_profit_price = Number(parseFloat(tpPrice).toFixed(pricePrecision));
            }

            if (slPercentage) {
                const percentage = parseFloat(slPercentage);
                const slPrice = isLong 
                    ? entryPrice * (1 - percentage/100)
                    : entryPrice * (1 + percentage/100);
                requestBody.stop_loss_price = Number(slPrice.toFixed(pricePrecision));
            } else if (slPrice) {
                requestBody.stop_loss_price = Number(parseFloat(slPrice).toFixed(pricePrecision));
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
                setShowTPSLDialog(false);
                setTpPercentage('');
                setSlPercentage('');
                setTpPrice('');
                setSlPrice('');
            }
        } catch (error) {
            console.error('Error setting TP/SL:', error);
            setError(error instanceof Error ? error.message : 'Failed to set TP/SL');
        } finally {
            setIsSettingTPSL(false);
        }
    };

    const handleCloseLimitOrders = async (orderType?: 'TP' | 'SL') => {
        try {
            if (orderType === 'TP') {
                setIsClosingTP(true);
            } else if (orderType === 'SL') {
                setIsClosingSL(true);
            } else {
                setIsClosingLimit(true);
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
                setIsClosingTP(false);
            } else if (orderType === 'SL') {
                setIsClosingSL(false);
            } else {
                setIsClosingLimit(false);
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
    useEffect(() => {
        if (showTPSLDialog) {
            if (position.takeProfitPrice) {
                setTpPrice(position.takeProfitPrice);
                // Calculate percentage based on entry price
                const entryPrice = parseFloat(position.entryPrice);
                const tpPrice = parseFloat(position.takeProfitPrice);
                const tpPercentage = ((tpPrice - entryPrice) / entryPrice) * 100;
                setTpPercentage(tpPercentage.toFixed(2));
            }
            if (position.stopLossPrice) {
                setSlPrice(position.stopLossPrice);
                // Calculate percentage based on entry price
                const entryPrice = parseFloat(position.entryPrice);
                const slPrice = parseFloat(position.stopLossPrice);
                const slPercentage = ((slPrice - entryPrice) / entryPrice) * 100;
                setSlPercentage(slPercentage.toFixed(2));
            }
        }
    }, [showTPSLDialog, position.takeProfitPrice, position.stopLossPrice, position.entryPrice]);

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
                        onClick={() => setShowTPSLDialog(true)}
                        className={`flex items-center space-x-1 px-3 py-1 rounded-md 
                            ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
                        title="Set TP/SL"
                    >
                        <Target size={16} />
                        <span>Set TP/SL</span>
                    </button>
                    <button
                        onClick={() => setShowCloseConfirm(true)}
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
                            disabled={isClosingLimit}
                            className={`flex items-center space-x-1 px-2 py-1 rounded-md text-xs
                                ${isDarkMode ? 'bg-red-900 hover:bg-red-800' : 'bg-red-800 hover:bg-red-700'} text-white`}
                            title="Cancel All Orders"
                        >
                            <X size={14} />
                            <span>{isClosingLimit ? 'Canceling...' : 'Cancel All'}</span>
                        </button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        {position.takeProfitPrice && (
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Take Profit</span>
                                    <button
                                        onClick={() => handleCloseLimitOrders('TP')}
                                        disabled={isClosingTP}
                                        className={`flex items-center space-x-1 px-1.5 py-0.5 rounded-md text-xs
                                            ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white`}
                                        title="Cancel Take Profit"
                                    >
                                        <X size={12} />
                                        <span>{isClosingTP ? 'Canceling...' : 'Cancel'}</span>
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
                                        disabled={isClosingSL}
                                        className={`flex items-center space-x-1 px-1.5 py-0.5 rounded-md text-xs
                                            ${isDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-500 hover:bg-red-600'} text-white`}
                                        title="Cancel Stop Loss"
                                    >
                                        <X size={12} />
                                        <span>{isClosingSL ? 'Canceling...' : 'Cancel'}</span>
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
            {showTPSLDialog && (
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
                                    value={tpPercentage}
                                    onChange={(e) => setTpPercentage(e.target.value)}
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
                                    value={slPercentage}
                                    onChange={(e) => setSlPercentage(e.target.value)}
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
                                    value={tpPrice}
                                    onChange={(e) => setTpPrice(e.target.value)}
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
                                    value={slPrice}
                                    onChange={(e) => setSlPrice(e.target.value)}
                                    className={`mt-1 block w-full rounded-md ${isDarkMode ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2`}
                                    placeholder="Enter price"
                                />
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end space-x-3">
                            <button
                                onClick={() => setShowTPSLDialog(false)}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} text-sm font-medium`}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSetTPSL}
                                disabled={isSettingTPSL}
                                className={`px-4 py-2 rounded-md ${isDarkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white text-sm font-medium`}
                            >
                                {isSettingTPSL ? 'Setting...' : 'Set TP/SL'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Close Position Confirmation Dialog */}
            {showCloseConfirm && (
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
                                onClick={() => setShowCloseConfirm(false)}
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