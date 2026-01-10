import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService, Toast } from '../../services/notification.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.component.html',
})
export class ToastComponent {
  notificationService = inject(NotificationService);
  
  toasts = this.notificationService.toasts;

  remove(id: number) {
    this.notificationService.remove(id);
  }
}
