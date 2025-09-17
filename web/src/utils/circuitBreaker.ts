/**
 * Circuit Breaker Pattern Implementation
 * Prevents cascading failures by temporarily blocking requests to failing services
 */

interface CircuitBreakerOptions {
  failureThreshold?: number;  // Number of failures before opening circuit
  resetTimeout?: number;       // Time in ms before attempting to close circuit
  successThreshold?: number;   // Number of successes needed to close circuit
  timeout?: number;           // Request timeout in ms
}

enum CircuitState {
  CLOSED = 'CLOSED',     // Normal operation
  OPEN = 'OPEN',         // Blocking all requests
  HALF_OPEN = 'HALF_OPEN' // Testing if service recovered
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime?: number;
  private resetTimer?: NodeJS.Timeout;
  
  private readonly options: Required<CircuitBreakerOptions>;
  
  constructor(options: CircuitBreakerOptions = {}) {
    this.options = {
      failureThreshold: options.failureThreshold ?? 5,
      resetTimeout: options.resetTimeout ?? 60000, // 1 minute
      successThreshold: options.successThreshold ?? 3,
      timeout: options.timeout ?? 10000 // 10 seconds
    };
  }
  
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Check if circuit is open
    if (this.state === CircuitState.OPEN) {
      throw new Error('[CircuitBreaker] Circuit is OPEN - service unavailable');
    }
    
    try {
      // Add timeout wrapper
      const result = await this.withTimeout(fn(), this.options.timeout);
      
      // Record success
      this.onSuccess();
      
      return result;
    } catch (error) {
      // Record failure
      this.onFailure();
      
      throw error;
    }
  }
  
  private async withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) => 
        setTimeout(() => reject(new Error('[CircuitBreaker] Request timeout')), timeout)
      )
    ]);
  }
  
  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      
      if (this.successCount >= this.options.successThreshold) {
        console.log('[CircuitBreaker] Circuit CLOSED - service recovered');
        this.state = CircuitState.CLOSED;
        this.successCount = 0;
      }
    }
  }
  
  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.options.failureThreshold) {
      console.log('[CircuitBreaker] Circuit OPEN - too many failures');
      this.state = CircuitState.OPEN;
      
      // Schedule circuit reset attempt
      if (this.resetTimer) {
        clearTimeout(this.resetTimer);
      }
      
      this.resetTimer = setTimeout(() => {
        console.log('[CircuitBreaker] Circuit HALF_OPEN - testing recovery');
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      }, this.options.resetTimeout);
    }
  }
  
  getState(): CircuitState {
    return this.state;
  }
  
  getStats() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime
    };
  }
  
  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = undefined;
    
    if (this.resetTimer) {
      clearTimeout(this.resetTimer);
      this.resetTimer = undefined;
    }
  }
}

/**
 * Circuit Breaker Manager for managing multiple circuit breakers
 */
export class CircuitBreakerManager {
  private breakers = new Map<string, CircuitBreaker>();
  
  getBreaker(name: string, options?: CircuitBreakerOptions): CircuitBreaker {
    let breaker = this.breakers.get(name);
    
    if (!breaker) {
      breaker = new CircuitBreaker(options);
      this.breakers.set(name, breaker);
    }
    
    return breaker;
  }
  
  async execute<T>(name: string, fn: () => Promise<T>, options?: CircuitBreakerOptions): Promise<T> {
    const breaker = this.getBreaker(name, options);
    return breaker.execute(fn);
  }
  
  getStats() {
    const stats: Record<string, any> = {};
    
    this.breakers.forEach((breaker, name) => {
      stats[name] = breaker.getStats();
    });
    
    return stats;
  }
  
  reset(name?: string): void {
    if (name) {
      this.breakers.get(name)?.reset();
    } else {
      this.breakers.forEach(breaker => breaker.reset());
    }
  }
}

// Global circuit breaker manager instance
export const circuitBreakerManager = new CircuitBreakerManager();