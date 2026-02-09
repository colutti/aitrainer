import { cn } from '../../utils/cn';

import { Pagination } from './Pagination';

interface DataListProps<T> {
  title?: React.ReactNode;
  description?: string;
  actions?: React.ReactNode;
  headerContent?: React.ReactNode;
  
  data: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
  
  isLoading?: boolean;
  layout?: 'list' | 'grid';
  emptyState: {
    icon?: React.ReactNode;
    title: string;
    description: string;
    action?: React.ReactNode;
  };
  
  pagination?: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
  
  className?: string;
  gridClassName?: string;
}

/**
 * DataList component
 * 
 * A standardized component for displaying lists of data with consistent 
 * styling, empty states, and pagination.
 */
export function DataList<T>({
  title,
  description,
  actions,
  headerContent,
  data,
  renderItem,
  keyExtractor,
  isLoading = false,
  layout = 'list',
  emptyState,
  pagination,
  className,
  gridClassName,
}: DataListProps<T>) {
  
  // Loading State
  if (isLoading && data.length === 0) {
    return (
      <div className={cn("space-y-6", className)}>
        {(title ?? actions) && (
          <div className="flex items-center justify-between mb-6">
            <div>
              {title && <div className="h-8 w-48 bg-dark-card rounded-lg animate-pulse mb-2" />}
              {description && <div className="h-4 w-64 bg-dark-card rounded-lg animate-pulse" />}
            </div>
            {actions && <div className="h-10 w-32 bg-dark-card rounded-lg animate-pulse" />}
          </div>
        )}
        
        {headerContent}

        <div className={cn(
          "gap-4",
          layout === 'grid' 
            ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3" 
            : "flex flex-col",
            gridClassName
        )}>
          {[1, 2, 3].map((i) => (
            <div 
              key={i} 
              className={cn(
                "bg-dark-card rounded-2xl animate-pulse",
                layout === 'grid' ? "h-64" : "h-24"
              )} 
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500", className)}>
      {/* Header Section */}
      {(title ?? description ?? actions) && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            {title && (
              <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-text-secondary mt-1">
                {description}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex gap-2">
              {actions}
            </div>
          )}
        </div>
      )}
      
      {/* Custom Header Content (Filters, Search, etc) */}
      {headerContent}

      {/* Content */}
      {data.length > 0 ? (
        <>
          <div className={cn(
            "gap-4",
            layout === 'grid' 
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3" 
              : "flex flex-col",
            gridClassName
          )}>
            {data.map((item) => (
              <div key={keyExtractor(item)} className="w-full">
                {renderItem(item)}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination && (
            <Pagination
              currentPage={pagination.currentPage}
              totalPages={pagination.totalPages}
              onPageChange={pagination.onPageChange}
              isLoading={isLoading}
            />
          )}
        </>
      ) : (
        /* Empty State */
        <div className="bg-dark-card border border-border border-dashed rounded-3xl p-12 text-center">
          {emptyState.icon && (
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 text-text-muted">
              {emptyState.icon}
            </div>
          )}
          <h3 className="text-xl font-bold text-text-primary">{emptyState.title}</h3>
          <p className="text-text-secondary mt-2 max-w-xs mx-auto">
            {emptyState.description}
          </p>
          {emptyState.action && (
            <div className="mt-6">
              {emptyState.action}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
