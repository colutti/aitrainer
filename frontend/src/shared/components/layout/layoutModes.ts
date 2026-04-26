export interface LayoutMode {
  contentClassName: string;
  navClassName: string;
}

export function getLayoutMode(pathname: string): LayoutMode {
  if (pathname.startsWith('/dashboard/chat')) {
    return {
      contentClassName: 'max-w-[2160px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  if (pathname === '/dashboard' || pathname.startsWith('/dashboard/body') || pathname.startsWith('/dashboard/nutrition') || pathname.startsWith('/dashboard/workouts')) {
    return {
      contentClassName: 'max-w-[1920px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  return {
    contentClassName: 'max-w-[1600px] px-4 md:px-8 xl:px-10',
    navClassName: 'px-4 md:px-8 xl:px-10',
  };
}
