import type { TFunction } from 'i18next';
import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from './Button';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundaryClass extends Component<Props & { t: TFunction }, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center bg-dark-card border border-red-500/20 rounded-xl space-y-4">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
            <AlertTriangle size={32} />
          </div>
          <div className="space-y-2">
            <h3 className="text-xl font-black text-text-primary tracking-tight">
              {this.props.t('errors.server_error')}
            </h3>
            <p className="text-text-secondary max-w-xs mx-auto">
              {this.props.t('errors.default')}
            </p>
          </div>
          <Button 
            variant="secondary" 
            onClick={this.handleReset}
            className="flex items-center gap-2"
          >
            <RefreshCcw size={16} />
            {this.props.t('errors.retry')}
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

export const GlobalErrorBoundary = ({ children, fallback }: Props) => {
  const { t } = useTranslation();
  return (
    <ErrorBoundaryClass t={t} fallback={fallback}>
      {children}
    </ErrorBoundaryClass>
  );
};
