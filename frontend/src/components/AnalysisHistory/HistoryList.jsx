import { useEffect, useState } from 'react';
import { Pagination } from 'react-bootstrap';
import { toast } from 'react-toastify';
import AnalysisService from '../../services/AnalysisService';

const HistoryList = ({ user }) => {
  const [history, setHistory] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    pages: 1
  });
  const [loading, setLoading] = useState(false);

  const fetchHistory = async (page = 1) => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await AnalysisService.getHistory(page, pagination.per_page);
      setHistory(response.history);
      setPagination(response.pagination);
    } catch (error) {
      toast.error(`Failed to load history: ${error}`);
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

  if (!user) {
    return (
      <div className="alert alert-info">
        Please log in to view your analysis history
      </div>
    );
  }

  return (
    <div className="history-list">
      <h2 className="mb-4">Analysis History</h2>
      
      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      ) : history.length === 0 ? (
        <div className="alert alert-info">
          No analysis history found. Perform your first analysis!
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Date</th>
                  <th>Coverage</th>
                  <th>Severity</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map(item => (
                  <tr key={item.id}>
                    <td>
                      <span className={`badge ${
                        item.type === 'detect' ? 'bg-primary' : 'bg-warning'
                      }`}>
                        {item.type === 'detect' ? 'Detection' : 'Prediction'}
                      </span>
                    </td>
                    <td>
                      {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                    </td>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.result.coverage}%</td>
                    <td>
                      <span className={`badge ${
                        item.result.severity === 'high' ? 'bg-danger' : 
                        item.result.severity === 'medium' ? 'bg-warning' : 'bg-success'
                      }`}>
                        {item.result.severity}
                      </span>
                    </td>
                    <td>
                      <a 
                        href={item.image_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-outline-primary"
                      >
                        View
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {pagination.pages > 1 && (
            <Pagination className="justify-content-center mt-4">
              <Pagination.Prev 
                disabled={pagination.page === 1} 
                onClick={() => handlePageChange(pagination.page - 1)} 
              />
              
              {[...Array(pagination.pages).keys()].map(page => (
                <Pagination.Item
                  key={page + 1}
                  active={page + 1 === pagination.page}
                  onClick={() => handlePageChange(page + 1)}
                >
                  {page + 1}
                </Pagination.Item>
              ))}
              
              <Pagination.Next 
                disabled={pagination.page === pagination.pages} 
                onClick={() => handlePageChange(pagination.page + 1)} 
              />
            </Pagination>
          )}
        </>
      )}
    </div>
  );
};

export default HistoryList;