import { Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';


@Injectable({
    providedIn: 'root'  
  })
export class ToastrMessage{
constructor(private toastr:ToastrService){}

error(title:string,message:string){
    this.toastr.error(message,title)
}
success(title:string,message:string){
    this.toastr.success(message,title)
}
info(title:string,message:string){
    this.toastr.info(message,title)
}

}