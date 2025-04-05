import React, { useState } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageCarouselProps {
    images: {
        url: string;
        label: string;
    }[];
    className?: string;
}

export function ImageCarousel({ images, className }: ImageCarouselProps) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const nextImage = () => {
        setCurrentIndex((prev) => (prev + 1) % images.length);
    };

    const previousImage = () => {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    // Handle empty images array
    if (!images || images.length === 0) {
        return (
            <div className={cn("relative aspect-square overflow-hidden rounded-lg bg-gray-100 flex items-center justify-center", className)}>
                <p className="text-gray-500">No images available</p>
            </div>
        );
    }

    return (
        <>
            <div className={cn("relative group", className)}>
                <div className="relative aspect-square overflow-hidden rounded-lg">
                    <img
                        src={images[currentIndex]?.url}
                        alt={images[currentIndex]?.label || 'Image'}
                        className="object-cover w-full h-full cursor-pointer transition-transform hover:scale-105"
                        onClick={() => setIsModalOpen(true)}
                    />

                    {images.length > 1 && (
                        <>
                            <button
                                onClick={previousImage}
                                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                aria-label="Previous image"
                            >
                                <ChevronLeft className="h-6 w-6" />
                            </button>
                            <button
                                onClick={nextImage}
                                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                aria-label="Next image"
                            >
                                <ChevronRight className="h-6 w-6" />
                            </button>
                        </>
                    )}

                    <div className="absolute bottom-2 left-1/2 -translate-x-1/2 bg-black/50 text-white px-3 py-1 rounded-full text-sm">
                        {images[currentIndex]?.label || 'Image'}
                    </div>
                </div>
            </div>

            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="max-w-[95vw] h-[95vh] p-0 overflow-hidden flex items-center justify-center">
                    <div className="relative w-full h-full flex items-center justify-center">
                        <button
                            onClick={() => setIsModalOpen(false)}
                            className="absolute right-2 top-2 bg-black/50 text-white p-2 rounded-full z-50"
                            aria-label="Close modal"
                        >
                            <X className="h-6 w-6" />
                        </button>

                        <div className="relative w-full h-full flex items-center justify-center">
                            <img
                                src={images[currentIndex]?.url}
                                alt={images[currentIndex]?.label || 'Image'}
                                className="max-w-full max-h-full object-contain"
                            />

                            {images.length > 1 && (
                                <>
                                    <button
                                        onClick={previousImage}
                                        className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full"
                                        aria-label="Previous image"
                                    >
                                        <ChevronLeft className="h-6 w-6" />
                                    </button>
                                    <button
                                        onClick={nextImage}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full"
                                        aria-label="Next image"
                                    >
                                        <ChevronRight className="h-6 w-6" />
                                    </button>
                                </>
                            )}

                            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 bg-black/50 text-white px-3 py-1 rounded-full text-sm">
                                {images[currentIndex]?.label || 'Image'}
                            </div>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
} 