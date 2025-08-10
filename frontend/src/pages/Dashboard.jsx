import { useState } from 'react';
import { Card, Col, Container, Row } from 'react-bootstrap';
import AnalysisResult from '../components/AnalysisResult';
import WaterAnalysisMap from '../components/Map/WaterAnalysisMap';

const Dashboard = ({ user }) => {
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result);
  };

  return (
    <Container fluid className="py-4">
      <Row>
        <Col lg={8}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Water Analysis Map</Card.Title>
              <WaterAnalysisMap 
                user={user} 
                onAnalysisComplete={handleAnalysisComplete} 
              />
            </Card.Body>
          </Card>
        </Col>
        
        <Col lg={4}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Latest Analysis Result</Card.Title>
              {analysisResult ? (
                <AnalysisResult result={analysisResult} />
              ) : (
                <div className="text-center py-4">
                  <p>Perform an analysis to see results</p>
                </div>
              )}
            </Card.Body>
          </Card>
          
          <Card>
            <Card.Body>
              <Card.Title>Quick Stats</Card.Title>
              <div className="d-flex justify-content-around text-center py-3">
                <div>
                  <h4>12</h4>
                  <p className="text-muted mb-0">Analyses</p>
                </div>
                <div>
                  <h4>3.2 km²</h4>
                  <p className="text-muted mb-0">Covered</p>
                </div>
                <div>
                  <h4>8</h4>
                  <p className="text-muted mb-0">Locations</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;