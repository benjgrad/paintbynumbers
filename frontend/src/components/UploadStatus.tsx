import React, { useEffect, useState } from 'react';
import { ImageCarousel } from './ImageCarousel';
import { Loader2 } from 'lucide-react';

interface UploadStatusProps {
    uploadId: string;
    initialStatus?: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
}

interface UploadDetails {
    id: string;
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    filename: string;
    processedFilename?: string;
    filledFilename?: string;
    errorMessage?: string;
}

const BACKEND_URL = 'http://localhost:8000';

export function UploadStatus({ uploadId, initialStatus = 'PENDING' }: UploadStatusProps) {
    const [uploadDetails, setUploadDetails] = useState<UploadDetails | null>(null);
    const [isPolling, setIsPolling] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/api/uploads/${uploadId}`);
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Server responded with status ${response.status}`);
                }
                const data = await response.json();
                setUploadDetails(data);
                setError(null);

                // Stop polling if we reach a final state
                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                    setIsPolling(false);
                }
            } catch (error) {
                console.error('Error checking upload status:', error);
                setError(error instanceof Error ? error.message : 'Failed to fetch upload status');
                setIsPolling(false);
            }
        };

        // Initial check
        checkStatus();

        // Set up polling if not in a final state
        let pollInterval: NodeJS.Timeout;
        if (isPolling) {
            pollInterval = setInterval(checkStatus, 2000); // Poll every 2 seconds
        }

        return () => {
            if (pollInterval) clearInterval(pollInterval);
        };
    }, [uploadId, isPolling]);

    if (error) {
        return (
            <div className="p-4 text-red-500">
                {error}
            </div>
        );
    }

    if (!uploadDetails) {
        return (
            <div className="flex items-center justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin" />
            </div>
        );
    }

    if (uploadDetails.status === 'FAILED') {
        return (
            <div className="p-4 text-red-500">
                Error processing image: {uploadDetails.errorMessage || 'Unknown error'}
            </div>
        );
    }

    if (uploadDetails.status === 'PENDING' || uploadDetails.status === 'PROCESSING') {
        return (
            <div className="flex flex-col items-center justify-center p-4 space-y-2">
                <Loader2 className="h-6 w-6 animate-spin" />
                <p className="text-sm text-gray-500">
                    {uploadDetails.status === 'PENDING' ? 'Waiting to process...' : 'Processing your image...'}
                </p>
            </div>
        );
    }

    // For completed uploads, show the carousel
    const images = [];

    if (uploadDetails.processedFilename) {
        images.push({
            url: `${BACKEND_URL}/uploads/${uploadDetails.processedFilename}`,
            label: 'Paint by Numbers Template'
        });
    }

    if (uploadDetails.filledFilename) {
        images.push({
            url: `${BACKEND_URL}/uploads/${uploadDetails.filledFilename}`,
            label: 'Color Reference'
        });
    }

    return (
        <div className="p-4">
            <ImageCarousel
                images={images}
                className="max-w-xl mx-auto"
            />
        </div>
    );
} 