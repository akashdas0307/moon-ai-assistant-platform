import React from 'react';

interface ImageViewerProps {
  path: string;
  name: string;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({ path, name }) => {
  // Use relative path due to Vite proxy
  const imageUrl = `/api/v1/files/content?path=${encodeURIComponent(path)}`;

  return (
    <div className="flex items-center justify-center h-full bg-[#1a1a1a] p-4">
      <img
        src={imageUrl}
        alt={name}
        className="max-w-full max-h-full object-contain"
      />
    </div>
  );
};
