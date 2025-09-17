import React, { useState } from 'react';
import { Image, X, ZoomIn } from 'lucide-react';

interface ImageData {
  url: string;
  caption?: string;
  uploaded_at?: string;
  analysis?: string;
}

interface ImageGalleryProps {
  images: (string | ImageData)[];
  maxDisplayed?: number;
  className?: string;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ 
  images, 
  maxDisplayed = 3, 
  className = '' 
}) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  if (!images || images.length === 0) {
    return null;
  }

  // Normalize images to consistent format
  const normalizedImages: ImageData[] = images.map((img, index) => {
    if (typeof img === 'string') {
      return {
        url: img,
        caption: `Image ${index + 1}`
      };
    }
    return img;
  });

  const displayImages = showAll ? normalizedImages : normalizedImages.slice(0, maxDisplayed);
  const hasMore = normalizedImages.length > maxDisplayed;

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Image Grid */}
      <div className={`grid gap-2 ${displayImages.length === 1 ? 'grid-cols-1' : displayImages.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
        {displayImages.map((image, index) => (
          <div
            key={index}
            className="relative group cursor-pointer overflow-hidden rounded-lg bg-gray-100"
            onClick={() => setSelectedImage(image.url)}
          >
            <div className="aspect-square">
              <img
                src={image.url}
                alt={image.caption || `Upload ${index + 1}`}
                className="w-full h-full object-cover transition-transform group-hover:scale-105"
                loading="lazy"
              />
              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            
            {/* Show +N overlay on last image if there are more */}
            {index === maxDisplayed - 1 && hasMore && !showAll && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                <span className="text-white font-semibold text-lg">
                  +{normalizedImages.length - maxDisplayed}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Image counter and expand button */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Image className="w-4 h-4" />
          <span>{normalizedImages.length} image{normalizedImages.length !== 1 ? 's' : ''}</span>
        </div>
        
        {hasMore && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            {showAll ? 'Show less' : `View all ${normalizedImages.length}`}
          </button>
        )}
      </div>

      {/* Fullscreen modal */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 z-10 p-2 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedImage}
              alt="Fullscreen view"
              className="max-w-full max-h-full object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageGallery;