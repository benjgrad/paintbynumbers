'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Toaster, toast } from "sonner"
import { useRouter } from 'next/navigation'
import { UploadStatus } from '@/components/UploadStatus'

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [colorCount, setColorCount] = useState([20]) // Slider returns array
  const router = useRouter()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setUploadId(null) // Reset upload ID when new file is selected
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error("Please select an image file to upload.")
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('color_count', colorCount[0].toString())

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        toast.success('Image uploaded successfully')
        setUploadId(data.id) // Store the upload ID
      } else {
        throw new Error(data.error || 'Upload failed')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to upload image')
      setUploadId(null)
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Image Upload</CardTitle>
            <CardDescription>
              Select an image file to upload and convert to a paint by numbers template.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid w-full max-w-sm items-center gap-1.5">
              <Input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="cursor-pointer"
                disabled={uploading}
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Number of Colors</span>
                <span className="font-medium">{colorCount[0]}</span>
              </div>
              <Slider
                value={colorCount}
                onValueChange={setColorCount}
                min={2}
                max={30}
                step={1}
                disabled={uploading}
              />
              <p className="text-xs text-gray-500">
                Choose between 2 and 30 colors for your paint by numbers template.
              </p>
            </div>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className="w-full"
            >
              {uploading ? 'Uploading...' : 'Upload Image'}
            </Button>
          </CardContent>
        </Card>

        {uploadId && (
          <Card>
            <CardHeader>
              <CardTitle>Processing Status</CardTitle>
              <CardDescription>
                Your image is being converted to a paint by numbers template with {colorCount[0]} colors.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <UploadStatus uploadId={uploadId} />
            </CardContent>
          </Card>
        )}

        <div className="text-center">
          <Button
            variant="outline"
            onClick={() => router.push('/uploads')}
          >
            View All Uploads
          </Button>
        </div>
      </div>
      <Toaster />
    </main>
  )
}
