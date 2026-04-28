export interface LayoutMode {
  shellClassName: string;
  mainClassName: string;
  contentClassName: string;
  navClassName: string;
}

export function getLayoutMode(pathname: string): LayoutMode {
  if (pathname.startsWith('/dashboard/chat')) {
    return {
      shellClassName: 'app-shell--conversation',
      mainClassName: 'app-shell-main--conversation',
      contentClassName: 'max-w-[2160px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  if (pathname === '/dashboard' || pathname.startsWith('/dashboard/body') || pathname.startsWith('/dashboard/nutrition') || pathname.startsWith('/dashboard/workouts')) {
    return {
      shellClassName: 'app-shell--workspace',
      mainClassName: 'app-shell-main--workspace',
      contentClassName: 'max-w-[1920px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  return {
    shellClassName: 'app-shell--default',
    mainClassName: 'app-shell-main--default',
    contentClassName: 'max-w-[1600px] px-4 md:px-8 xl:px-10',
    navClassName: 'px-4 md:px-8 xl:px-10',
  };
}
