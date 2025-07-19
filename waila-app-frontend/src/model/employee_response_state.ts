export class EmployeeResponse {
    answer: string;
    human_intervention_query_arr:any;
    isFeedBackFromUser: boolean;
    options_query_arr:any;
  
    constructor(
      answer: string,
      human_intervention_query_arr: [],
      isFeedBackFromUser: boolean,
      options_query_arr:any
    ) {
      this.answer = answer;
      this.human_intervention_query_arr = human_intervention_query_arr;
      this.isFeedBackFromUser = isFeedBackFromUser;
      this.options_query_arr=options_query_arr
    }
  }