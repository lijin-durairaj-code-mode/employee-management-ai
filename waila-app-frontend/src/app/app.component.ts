import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';


//constants
const BASE_URL='http://127.0.0.1:8000/'

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'waila-app-fronend';
  myForm: FormGroup;
  resolution_arr:any=[]
  loader=false

  constructor(private fb:FormBuilder, private http:HttpClient){
    this.myForm = this.fb.group({
      aq: ['', Validators.required]
    });
  }

  ngOnInit(){
    this.http.get(BASE_URL)
    .subscribe(res=>{
      console.log(res)
    })
  }


  onSubmit() {
    if (this.myForm.valid) {
      this.loader=true
      let request={
        'query':this.myForm.controls['aq'].value
      }
      this.http.post(BASE_URL+'question',request)
      .subscribe(res=>{
        this.loader=false;        
        this.resolution_arr.push({
          'question':this.myForm.controls['aq'].value,
          'answer':res
         })
      },()=>{
        this.loader=false;  
        alert('error')
      },()=>{
        this.myForm.reset();
      })
    } 
  }
}
