
import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NotFound from './pages/NotFound';

export default function App(){
  return (
    <div>
      <nav style={{padding:10}}><Link to='/'>Dashboard</Link> | <Link to='/login'>Login</Link></nav>
      <Routes>
        <Route path='/' element={<Dashboard/>} />
        <Route path='/login' element={<Login/>} />
        <Route path='*' element={<NotFound/>} />
      </Routes>
    </div>
  );
}
