import React, { useState, useEffect } from 'react';
import { Modal, Button, Image, Spin, Alert, Tabs } from 'antd';
import { EyeOutlined, PictureOutlined, FileImageOutlined } from '@ant-design/icons';
import type { TabsProps } from 'antd';

interface BidCardImage {
  photo_id: string;
  filename: string;
  description: string;
  type: string;
  source: string;
  uploaded_at: string;
  contractor_request?: string;
}

interface RFIPhotos {
  rfi_photos: BidCardImage[];
}

interface ProjectImage {
  url: string;
  filename: string;
  type: string;
  description?: string;
}

interface BidCardImagesViewerProps {
  bidCardId: string;
  bidCardNumber: string;
  visible: boolean;
  onClose: () => void;
}

const BidCardImagesViewer: React.FC<BidCardImagesViewerProps> = ({
  bidCardId,
  bidCardNumber,
  visible,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [rfiPhotos, setRfiPhotos] = useState<BidCardImage[]>([]);
  const [projectImages, setProjectImages] = useState<ProjectImage[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible && bidCardId) {
      fetchBidCardImages();
    }
  }, [visible, bidCardId]);

  const fetchBidCardImages = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch bid card data including RFI photos and project images
      const response = await fetch(`/api/bid-cards/${bidCardId}/images`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch images: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Extract RFI photos
      if (data.rfi_photos && Array.isArray(data.rfi_photos)) {
        setRfiPhotos(data.rfi_photos);
      }
      
      // Extract project images
      if (data.project_images && Array.isArray(data.project_images)) {
        setProjectImages(data.project_images);
      }
      
    } catch (error) {
      console.error('Error fetching bid card images:', error);
      setError(error instanceof Error ? error.message : 'Failed to load images');
    } finally {
      setLoading(false);
    }
  };

  const renderRFIPhotos = () => {
    if (!rfiPhotos || rfiPhotos.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <PictureOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <p>No RFI photos available</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {rfiPhotos.map((photo, index) => (
          <div key={photo.photo_id || index} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-900">{photo.filename}</h4>
                  <p className="text-sm text-gray-600 mt-1">{photo.description}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>Type: {photo.type.replace('_', ' ').toUpperCase()}</span>
                    <span>Source: {photo.source}</span>
                    <span>Uploaded: {new Date(photo.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <FileImageOutlined className="text-blue-500" />
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">RFI</span>
                </div>
              </div>
              {photo.contractor_request && (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-sm text-blue-800">
                    <strong>Contractor Request:</strong> {photo.contractor_request}
                  </p>
                </div>
              )}
            </div>
            
            <div className="p-4">
              <div className="bg-gray-100 border border-gray-300 rounded p-4 text-center">
                <PictureOutlined style={{ fontSize: '48px', color: '#d1d5db' }} />
                <p className="mt-2 text-sm text-gray-600">
                  Image preview would appear here
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  File: {photo.filename}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderProjectImages = () => {
    if (!projectImages || projectImages.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <PictureOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <p>No project images available</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projectImages.map((image, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="aspect-w-16 aspect-h-9 bg-gray-100">
              <Image
                src={image.url}
                alt={image.filename}
                className="object-cover w-full h-48"
                placeholder={
                  <div className="flex items-center justify-center h-48 bg-gray-100">
                    <PictureOutlined style={{ fontSize: '48px', color: '#d1d5db' }} />
                  </div>
                }
              />
            </div>
            <div className="p-3">
              <h4 className="font-semibold text-sm text-gray-900">{image.filename}</h4>
              {image.description && (
                <p className="text-xs text-gray-600 mt-1">{image.description}</p>
              )}
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded mt-2 inline-block">
                {image.type || 'Project Image'}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const tabItems: TabsProps['items'] = [
    {
      key: '1',
      label: (
        <span>
          <FileImageOutlined />
          RFI Photos ({rfiPhotos.length})
        </span>
      ),
      children: renderRFIPhotos(),
    },
    {
      key: '2', 
      label: (
        <span>
          <PictureOutlined />
          Project Images ({projectImages.length})
        </span>
      ),
      children: renderProjectImages(),
    },
  ];

  return (
    <Modal
      title={
        <div className="flex items-center space-x-2">
          <EyeOutlined />
          <span>Bid Card Images - {bidCardNumber}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          Close
        </Button>
      ]}
      width={800}
      style={{ top: 20 }}
    >
      {loading ? (
        <div className="text-center py-8">
          <Spin size="large" />
          <p className="mt-4">Loading images...</p>
        </div>
      ) : error ? (
        <Alert
          message="Error Loading Images"
          description={error}
          type="error"
          showIcon
        />
      ) : (
        <div className="max-h-[70vh] overflow-y-auto">
          <Tabs defaultActiveKey="1" items={tabItems} />
        </div>
      )}
    </Modal>
  );
};

export default BidCardImagesViewer;