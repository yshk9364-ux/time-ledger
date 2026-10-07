import {useEffect,useRef} from 'react';
export function SettingsModal({children,onClose}:{children:React.ReactNode;onClose:()=>void}){
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{
    const dialog=ref.current!;dialog.showModal();
    const old=document.body.style.overflow;document.body.style.overflow='hidden';
    return()=>{document.body.style.overflow=old;dialog.close()};
  },[]);
  return <dialog ref={ref} className="settings-dialog" aria-labelledby="settings-title" onClose={onClose} onCancel={onClose} onClick={event=>{
    if(event.target!==event.currentTarget)return;
    const r=event.currentTarget.getBoundingClientRect();
    if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)onClose();
  }}><div className="modal-header"><h2 id="settings-title">设置</h2><button type="button" className="quiet" onClick={onClose} aria-label="关闭设置">关闭 ×</button></div>{children}</dialog>;
}
