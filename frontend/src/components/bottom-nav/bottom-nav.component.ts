import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { NavigationService, View } from '../../services/navigation.service';

interface NavItem {
  id: View;
  label: string;
  iconName: string;
  isCenter?: boolean;
}

@Component({
  selector: 'app-bottom-nav',
  templateUrl: './bottom-nav.component.html',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
})
export class BottomNavComponent implements OnInit {
  currentView = this.navigationService.currentView;

  navItems: NavItem[] = [
    { id: 'home', label: 'Home', iconName: 'home' },
    { id: 'workouts', label: 'Treinos', iconName: 'dumbbell' },
    { id: 'coach', label: 'Coach', iconName: 'message-circle', isCenter: true },
    { id: 'body', label: 'Corpo', iconName: 'activity' },
    { id: 'profile', label: 'Perfil', iconName: 'user' },
  ];

  constructor(private navigationService: NavigationService) {}

  ngOnInit(): void {}

  navigate(viewId: View): void {
    this.navigationService.navigateTo(viewId);
  }

  isActive(viewId: string): boolean {
    return this.currentView() === viewId;
  }
}
