
import React, {useState} from 'react';
import axios from 'axios';
export default function Login(){
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const onSubmit=async(e)=>{e.preventDefault(); try{ const resp=await axios.post('/api/auth/login',{email,password}); alert('Logged in (token length:'+ (resp.data.token||'').length +')'); }catch(err){ alert(err.response?.data?.message || err.message); }}
  return (
    <div style={{padding:20}}>
      <h2>Login</h2>
      <form onSubmit={onSubmit}><input placeholder='email' value={email} onChange={e=>setEmail(e.target.value)} /><br/>
      <input placeholder='password' value={password} onChange={e=>setPassword(e.target.value)} type='password'/><br/>
      <button>Login</button></form>
    </div>
  );
}
