import { useEffect, useState } from 'react';
import { Alert, Container, Pagination, Spinner } from 'react-bootstrap';
import HistoryList from '../components/AnalysisHistory/HistoryList';
import AnalysisService from '../services/AnalysisService';

const HistoryPage = ({ user }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    pages: 1
  });

  const fetchHistory = async (page = 1) => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await AnalysisService.getHistory(page, pagination.per_page);
      setHistory(response.history);
      setPagination(response.pagination);
    } catch (error) {
      setError(error.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(pagination.page);
  }, [user, pagination.page]);

  const handlePageChange = (page) => {
    setPagination({ ...pagination, page });
  };

  return (
    <Container className="py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Analysis History</h1>
        <div>
          <span className="me-2">Items per page:</span>
          <select 
            className="form-select d-inline-block w-auto"
            value={pagination.per_page}
            onChange={(e) => setPagination({ 
              ...pagination, 
              per_page: parseInt(e.target.value),
              page: 1
            })}
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>
      </div>
      
      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      ) : error ? (
        <Alert variant="danger">{error}</Alert>
      ) : history.length === 0 ? (
        <Alert variant="info">
          No analysis history found. Perform your first analysis!
        </Alert>
      ) : (
        <>
          <HistoryList history={history} />
          
          {pagination.pages > 1 && (
            <div className="d-flex justify-content-center mt-4">
              <Pagination>
                <Pagination.Prev 
                  disabled={pagination.page === 1} 
                  onClick={() => handlePageChange(pagination.page - 1)} 
                />
                
                {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                  const pageNum = i + 1;
                  return (
                    <Pagination.Item
                      key={pageNum}
                      active={pageNum === pagination.page}
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </Pagination.Item>
                  );
                })}
                
                {pagination.pages > 5 && (
                  <Pagination.Ellipsis />
                )}
                
                <Pagination.Next 
                  disabled={pagination.page === pagination.pages} 
                  onClick={() => handlePageChange(pagination.page + 1)} 
                />
              </Pagination>
            </div>
          )}
        </>
      )}
    </Container>
  );
};

export default HistoryPage;