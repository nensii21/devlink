import React, { useState, useRef, ChangeEvent } from 'react';

interface ProfileBannerUploaderProps {
  initialBannerUrl?: string;
  onSave: (compressedBase64: string) => void;
}

export const ProfileBannerUploader: React.FC<ProfileBannerUploaderProps> = ({
  initialBannerUrl,
  onSave,
}) => {
  const [imageSrc, setImageSrc] = useState<string | null>(initialBannerUrl || null);
  const [dragging, setDragging] = useState<boolean>(false);
  const [offsetY, setOffsetY] = useState<number>(0);
  const [startY, setStartY] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file selection and compression
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        // Compress and resize image to fit reasonable banner dimensions (e.g. 1200x400 for 3:1 ratio)
        const canvas = document.createElement('canvas');
        const targetWidth = 1200;
        const targetHeight = 400; // 3:1 ratio
        canvas.width = targetWidth;
        canvas.height = targetHeight;

        const ctx = canvas.getContext('2d');
        if (ctx) {
          // Draw image centered / scaled
          ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
          // Compress to JPEG with 0.82 quality
          const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.82);
          setImageSrc(compressedDataUrl);
          setOffsetY(0);
        }
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  };

  // Drag to reposition handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setDragging(true);
    setStartY(e.clientY - offsetY);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    const newY = e.clientY - startY;
    // Restrict dragging boundaries
    setOffsetY(Math.max(-150, Math.min(150, newY)));
  };

  const handleMouseUp = () => {
    setDragging(false);
  };

  const handleRemove = () => {
    setImageSrc(null);
    setOffsetY(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleConfirmSave = () => {
    if (imageSrc) {
      onSave(imageSrc);
      alert('Banner successfully saved and updated!');
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100">
      <h2 className="text-xl font-bold mb-4">Customize Profile Banner</h2>
      <p className="text-sm text-slate-600 dark:text-slate-300 mb-6">
        Upload a banner image, drag to reposition within the 3:1 ratio frame, and preview your changes before saving.
      </p>

      {/* Banner Preview & Reposition Box (3:1 Aspect Ratio) */}
      <div
        className="relative w-full h-48 sm:h-64 bg-slate-100 dark:bg-slate-900 rounded-lg overflow-hidden cursor-move border border-slate-300 dark:border-slate-700 select-none flex items-center justify-center"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {imageSrc ? (
          <img
            src={imageSrc}
            alt="Profile Banner Preview"
            style={{ transform: `translateY(${offsetY}px)` }}
            className="absolute w-full object-cover pointer-events-none transition-transform duration-75"
          />
        ) : (
          <div className="text-center text-slate-400">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-sm">No banner uploaded. Click below to select one.</span>
          </div>
        )}
        {imageSrc && (
          <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2.5 py-1 rounded-md pointer-events-none backdrop-blur-sm">
            ↕ Drag to Reposition
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
          >
            {imageSrc ? 'Change Banner' : 'Upload Banner'}
          </button>

          {imageSrc && (
            <button
              onClick={handleRemove}
              className="px-4 py-2 bg-red-100 hover:bg-red-200 dark:bg-red-950/40 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300 text-sm font-medium rounded-lg transition-colors"
            >
              Remove Banner
            </button>
          )}
        </div>

        {imageSrc && (
          <button
            onClick={handleConfirmSave}
            className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
          >
            Save Changes
          </button>
        )}
      </div>
    </div>
  );
};
