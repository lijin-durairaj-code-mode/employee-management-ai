import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { ToastrMessage } from '../utils/toastr-message'
import { EmployeeResponse } from 'src/model/employee_response_state';


//constants
const BASE_URL='http://127.0.0.1:8000/'

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  providers:[ToastrMessage]
})
export class AppComponent implements OnInit {
  title = 'waila-app-fronend';
  myForm: FormGroup;
  resolution_arr:any=[]
  loader=false
  re_write_query_arr:any[]=[ ]

  constructor(private fb:FormBuilder
    , private http:HttpClient,private toastr:ToastrMessage){
    this.myForm = this.fb.group({
      aq: ['', Validators.required]
    });
  }

  ngOnInit(){
    // this.http.get(BASE_URL)
    // .subscribe(res=>{
    //   console.log(res)
    // },(error)=>{
    //   this.toastr.error('error',error)
    // },)
  }

  get_user_response(e:any){
    this.loader=true
    const input = e.target as HTMLInputElement;
    const label = document.querySelector(`label[for="${input.id}"]`);
    const labelText = label ? label.textContent?.trim() : 'No label found';
    this.re_write_query_arr=[];
  
    console.log('Selected text:', labelText);
    let request={
      'query':labelText
    }
    this.http.post<EmployeeResponse>(BASE_URL+'human_feedback',request)
    .subscribe(res=>{
      this.loader=false;
      this.resolution_arr.push({
        'question':this.myForm.controls['aq'].value,
        'answer':res.answer
       })
    },(error)=>{
      this.loader=false;
      this.toastr.error('error',error)
    })
  }

  

  onSubmit() {
    if (this.myForm.valid) {
      this.loader=true
      let request={
        'query':this.myForm.controls['aq'].value
      }
      this.http.post<EmployeeResponse>(BASE_URL+'question',request)
      .subscribe((res:EmployeeResponse)=>{
        this.loader=false;   
      if(res?.options_query_arr?.['answer'].length>0){
      let _d:any=res.options_query_arr;
      for(let i=0;i<_d['answer'].length;i++){
        this.re_write_query_arr.push(_d['answer'][i])
      }
      }else{
        this.resolution_arr.push({
          'question':this.myForm.controls['aq'].value,
          'answer':res.answer
         })
      }
        
      },(error)=>{
        this.loader=false;
        this.toastr.error('error',error)
      },()=>{
        this.myForm.reset();
      })
    } 
  }
}
