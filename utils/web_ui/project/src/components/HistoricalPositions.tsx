import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, History, ArrowUp, ArrowDown, ChevronDown } from 'lucide-react';
import { HistoricalPosition } from '../types';
import { LoadingSpinner } from './LoadingSpinner';

interface HistoricalPositionsProps {
  positions: HistoricalPosition[];
  loading?: boolean;
}

export function HistoricalPositions({ positions, loading = false }: HistoricalPositionsProps) {
  const navigate = useNavigate();
  const [visiblePositions, setVisiblePositions] = useState(5);

  const handleViewChart = (position: HistoricalPosition) => {
    const positionId = `${position.symbol}-${position.closedAt}`;
    navigate(`/position/${positionId}`, { state: { position } });
  }

  const handleShowMore = () => {
    setVisiblePositions(prev => prev + 5);
  }

  const displayedPositions = positions.slice(0, visiblePositions);
  const hasMorePositions = visiblePositions < positions.length;

  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300">
      <div className="flex items-center mb-6">
        <div className="p-3 bg-dark-accent-info/20 rounded-xl mr-4">
          <History className="w-6 h-6 text-dark-accent-info" />
        </div>
        <h2 className="text-2xl font-bold text-dark-text-primary">
          Recent Positions
        </h2>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" variant="white" />
        </div>
      ) : positions.length === 0 ? (
        <div className="text-center py-12">
          <History className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <p className="text-dark-text-muted text-lg">No historical positions</p>
          <p className="text-dark-text-disabled text-sm mt-2">
            Closed positions will appear here
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {displayedPositions.map((position, index) => {
              const duration = new Date(position.closedAt).getTime() - new Date(position.openedAt).getTime();
              const durationHours = Math.floor(duration / (1000 * 60 * 60));
              const durationMinutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
              
              return (
                <div 
                  key={`${position.symbol}-${position.closedAt}`}
                  className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-all duration-300 hover:bg-dark-bg-tertiary/70"
                >
                  {/* Header Row */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-dark-text-primary">{position.symbol}</h3>
                      <span className={`flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                        position.side === 'LONG' 
                          ? 'bg-dark-accent-success/20 text-dark-accent-success' 
                          : 'bg-dark-accent-error/20 text-dark-accent-error'
                      }`}>
                        {position.side === 'LONG' 
                          ? <ArrowUp className="w-3 h-3 mr-1" />
                          : <ArrowDown className="w-3 h-3 mr-1" />
                        }
                        {position.side}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className={`text-right ${
                        parseFloat(position.profit) >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'
                      }`}>
                        <div className="text-lg font-bold">
                          {parseFloat(position.profit) >= 0 ? '+' : ''}${parseFloat(position.profit).toFixed(2)}
                        </div>
                      </div>
                      <button
                        onClick={() => handleViewChart(position)}
                        className="flex items-center space-x-1 px-3 py-2 rounded-lg bg-dark-bg-secondary hover:bg-dark-accent-primary/20 text-dark-text-muted hover:text-dark-accent-primary border border-dark-border-secondary hover:border-dark-accent-primary transition-all duration-300"
                      >
                        <LineChart className="w-4 h-4" />
                        <span className="text-sm hidden sm:inline">Chart</span>
                      </button>
                    </div>
                  </div>

                  {/* Details Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-dark-text-muted block">Entry Price</span>
                      <span className="font-mono text-dark-text-primary">${parseFloat(position.entryPrice).toFixed(4)}</span>
                    </div>
                    <div>
                      <span className="text-dark-text-muted block">Exit Price</span>
                      <span className="font-mono text-dark-text-primary">${parseFloat(position.exitPrice).toFixed(4)}</span>
                    </div>
                    <div>
                      <span className="text-dark-text-muted block">Amount</span>
                      <span className="font-mono text-dark-text-primary">${parseFloat(position.amount).toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-dark-text-muted block">Duration</span>
                      <span className="text-dark-text-primary">
                        {durationHours > 0 ? `${durationHours}h ` : ''}{durationMinutes}m
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {hasMorePositions && (
            <div className="mt-6 text-center">
              <button
                onClick={handleShowMore}
                className="flex items-center justify-center mx-auto px-6 py-3 rounded-xl bg-dark-bg-tertiary hover:bg-dark-accent-primary/20 text-dark-text-muted hover:text-dark-accent-primary border border-dark-border-secondary hover:border-dark-accent-primary transition-all duration-300"
              >
                <ChevronDown className="w-4 h-4 mr-2" />
                <span>Show More ({positions.length - visiblePositions} remaining)</span>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
