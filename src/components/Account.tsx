import {useState,useEffect} from 'react';
import {online,request,loadOnline} from '../store';
export function Account({children}:{children:React.ReactNode}) {
  const [ready,setReady]=useState(!online);
  const [error,setError]=useState('');
  useEffect(()=>{
    if(!online)return;
    request('session')
      .catch(()=>request('login',{method:'POST',body:JSON.stringify({username:'admin',password:''})}))
      .then(async()=>{await loadOnline();setReady(true)})
      .catch(()=>setError('暂时无法连接在线账本，请检查网络后重试。'));
  },[]);
  if(!ready)return <main className="welcome"><div className="brand">◷ 时间账户</div><h1>{error?'连接暂时中断':'正在读取在线账本…'}</h1>{error&&<><p className="error">{error}</p><button onClick={()=>location.reload()}>重新连接</button></>}</main>;
  return <>{online&&<div className="account-bar"><span>在线共享账本 · 无需密码 · 手机电脑同步</span></div>}{children}</>;
}
