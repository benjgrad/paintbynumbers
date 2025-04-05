'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { UploadStatus } from '@/components/UploadStatus'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'

const BACKEND_URL = 'http://localhost:8000';

interface Upload {
    id: string;
    filename: string;
    originalName: string;
    status: string;
    processedFilename: string | null;
    filledFilename: string | null;
    errorMessage: string | null;
    createdAt: string;
    updatedAt: string;
}

export default function UploadsPage() {
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        const fetchUploads = async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/api/uploads`);
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Server responded with status ${response.status}`);
                }
                const data = await response.json();
                setUploads(data.uploads || []);
                setError(null);
            } catch (error) {
                console.error('Error fetching uploads:', error);
                const message = error instanceof Error ? error.message : 'Failed to fetch uploads';
                setError(message);
                toast.error(message);
            } finally {
                setLoading(false);
            }
        };

        fetchUploads();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen p-8 bg-gray-50 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen p-8 bg-gray-50">
                <div className="max-w-4xl mx-auto">
                    <Card>
                        <CardContent className="p-6">
                            <div className="text-center space-y-4">
                                <p className="text-red-500">{error}</p>
                                <Button onClick={() => router.push('/')}>
                                    Return to Upload Page
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <main className="min-h-screen p-8 bg-gray-50">
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="flex justify-between items-center">
                    <h1 className="text-2xl font-bold">Your Uploads</h1>
                    <Button onClick={() => router.push('/')}>Upload New Image</Button>
                </div>

                {uploads.length === 0 || uploads.length === undefined ? (
                    <Card>
                        <CardContent className="p-6 text-center text-gray-500">
                            No uploads found. Start by uploading an image.
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-6">
                        {uploads.map((upload) => (
                            <Card key={upload.id}>
                                <CardHeader>
                                    <CardTitle>{upload.originalName}</CardTitle>
                                    <CardDescription>
                                        Uploaded {new Date(upload.createdAt).toLocaleString()}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <UploadStatus
                                        uploadId={upload.id}
                                        initialStatus={upload.status as any}
                                    />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
} 