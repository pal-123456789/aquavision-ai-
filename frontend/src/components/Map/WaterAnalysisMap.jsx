import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useRef, useState } from 'react';
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet';
import { toast } from 'react-toastify';
import AnalysisService from '../../services/AnalysisService';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const LocationMarker = ({ position, setPosition }) => {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    }
  });

  return position ? (
    <Marker position={position} />
  ) : null;
};

const WaterAnalysisMap = ({ user, onAnalysisComplete }) => {
  const [position, setPosition] = useState(null);
  const [analysisType, setAnalysisType] = useState('detect');
  const [loading, setLoading] = useState(false);
  const mapRef = useRef();

  const handleAnalyze = async () => {
    if (!position) {
      toast.error('Please select a location on the map');
      return;
    }
    
    try {
      setLoading(true);
      let result;
      if (analysisType === 'detect') {
        result = await AnalysisService.detectAlgae(position.lat, position.lng);
      } else {
        result = await AnalysisService.predictAlgae(position.lat, position.lng);
      }
      
      onAnalysisComplete(result.result);
      toast.success('Analysis completed successfully!');
    } catch (error) {
      toast.error(`Analysis failed: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="map-container position-relative">
      <MapContainer
        center={[20.5937, 78.9629]} // Center on India
        zoom={5}
        ref={mapRef}
        style={{ height: '500px', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <LocationMarker position={position} setPosition={setPosition} />
      </MapContainer>
      
      <div className="map-controls card p-3">
        <div className="mb-3">
          <label className="form-label">Analysis Type</label>
          <select 
            className="form-select"
            value={analysisType}
            onChange={(e) => setAnalysisType(e.target.value)}
          >
            <option value="detect">Detect Current Algae</option>
            <option value="predict">Predict Future Spread</option>
          </select>
        </div>
        
        <button 
          className="btn btn-primary w-100"
          onClick={handleAnalyze}
          disabled={loading || !user}
        >
          {loading ? (
            <span className="spinner-border spinner-border-sm me-2" role="status"></span>
          ) : null}
          {user ? 'Analyze Water Quality' : 'Login to Analyze'}
        </button>
        
        {position && (
          <div className="mt-3">
            <p className="mb-1">Selected Location:</p>
            <p className="text-muted mb-0">Lat: {position.lat.toFixed(4)}, Lng: {position.lng.toFixed(4)}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WaterAnalysisMap;