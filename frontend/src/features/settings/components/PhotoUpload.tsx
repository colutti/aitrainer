import { Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { UserAvatar } from '../../../shared/components/ui/UserAvatar';

interface PhotoUploadProps {
  currentPhoto?: string | null;
  displayName?: string | null;
  email: string;
  onPhotoChange: (base64: string | null) => void;
  isLoading?: boolean;
}

/**
 * PhotoUpload component
 *
 * Allows users to upload, crop, and compress profile photos.
 * - Accepts JPEG, PNG, WEBP formats
 * - Crops to center square, resizes to 256x256
 * - Compresses to JPEG with progressive quality reduction
 * - Enforces 500KB max size
 */
export function PhotoUpload({
  currentPhoto,
  displayName,
  email,
  onPhotoChange,
  isLoading = false,
}: PhotoUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | undefined | null>(currentPhoto ?? undefined);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processImage = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          try {
            // Center-crop to square
            const size = Math.min(img.width, img.height);
            const sx = (img.width - size) / 2;
            const sy = (img.height - size) / 2;

            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const ctx = canvas.getContext('2d');
            if (!ctx) throw new Error('Failed to get canvas context');

            ctx.drawImage(img, sx, sy, size, size, 0, 0, 256, 256);

            // Try JPEG at decreasing quality until under 500KB
            let quality = 0.85;
            let dataUrl = canvas.toDataURL('image/jpeg', quality);

            while (dataUrl.length > 500_000 && quality > 0.3) {
              quality -= 0.1;
              dataUrl = canvas.toDataURL('image/jpeg', quality);
            }

            if (dataUrl.length > 500_000) {
              reject(new Error('Image too large even after compression'));
            } else {
              resolve(dataUrl);
            }
          } catch (err) {
            reject(err instanceof Error ? err : new Error(String(err)));
          }
        };
        img.onerror = () => {
          reject(new Error('Failed to load image'));
        };
        img.src = e.target?.result as string;
      };

      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsDataURL(file);
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setProcessing(true);

    void (async () => {
      try {
        const base64 = await processImage(file);
        setPreview(base64);
        onPhotoChange(base64);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to process image';
        setError(message);
        setPreview(undefined);
        onPhotoChange(null);
      } finally {
        setProcessing(false);
        // Reset input so same file can be selected again
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    })();
  };

  const handleRemove = () => {
    setPreview(undefined);
    setError(null);
    onPhotoChange(null);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const nameForDisplay = displayName ?? email.split('@')[0] ?? 'User';

  return (
    <div className="space-y-4">
      <div className="flex flex-col items-center gap-4">
        {/* Avatar Preview */}
        <div className="relative group">
          <UserAvatar photo={preview} name={nameForDisplay} size="2xl" />
          <button
            type="button"
            onClick={handleClick}
            disabled={processing || isLoading}
            className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Change profile photo"
          >
            <Upload size={24} className="text-white" />
          </button>
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          className="hidden"
          disabled={processing || isLoading}
        />

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            type="button"
            onClick={handleClick}
            disabled={processing || isLoading}
            size="sm"
            variant="secondary"
            className="gap-2"
          >
            <Upload size={16} />
            {preview ? 'Trocar foto' : 'Adicionar foto'}
          </Button>

          {preview && (
            <Button
              type="button"
              onClick={handleRemove}
              disabled={processing || isLoading}
              size="sm"
              variant="ghost"
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 gap-2"
            >
              <X size={16} />
              Remover
            </Button>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <p className="text-sm text-red-400 text-center max-w-xs">{error}</p>
        )}

        {/* Processing State */}
        {processing && (
          <p className="text-sm text-text-secondary text-center">Processando imagem...</p>
        )}
      </div>
    </div>
  );
}
