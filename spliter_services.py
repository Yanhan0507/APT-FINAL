#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'henry'

import webapp2
from constants import *
import logging, json
import uuid
from datetime import datetime
from model import User, Apartment, Expense, Item, Note, NoteBook, Reply, Task

class ServiceHandler(webapp2.RequestHandler):
    def respond(self, separators=(',', ':'), **response):
        if KEYWORD_ERROR in response and response[KEYWORD_ERROR]:
            #   record the error msg
            logging.error("Web Service Error: " + response[KEYWORD_ERROR])
        elif KEYWORD_STATUS in response:
            #   record the debugging status
            logging.debug("Web Service Debugging Information: " + response[KEYWORD_STATUS])

        if IDENTIFIER_JSON_MSG in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = IDENTIFIER_JSON_MSG

        return self.response.write(json.dumps(response, separators=separators))


class CreateAccountService(ServiceHandler):
    def get(self):

        # req_json = json.loads(self.request.body)


        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        # check whether this email has been used or not
        users = User.query(User.user_email == user_email).fetch()
        if len(users) > 0:
            response = {}
            response['error'] = 'the email: ' + user_email + ' has already been used'
            return self.respond(**response)

        # nick_name = req_json[IDENTIFIER_NICE_NAME]
        nick_name = self.request.get(IDENTIFIER_USER_NAME)
        # bank_account and user photo are not required
        bank_account = None
        cover_url = None
        # if IDENTIFIER_BANK_ACCOUNT in req_json:
        #     bank_account = req_json[IDENTIFIER_BANK_ACCOUNT]
        # if IDENTIFIER_USER_PHOTO in req_json:
        #     cover_url = req_json[IDENTIFIER_USER_PHOTO]
        bank_account = self.request.get(IDENTIFIER_BANK_ACCOUNT)
        new_user = User(user_email = user_email,
                        nick_name = nick_name,
                        bank_account = bank_account,
                        cover_url = cover_url,
                        owe = INITIAL_BALANCE,
                        cost = 0,
                        borrow = 0
                        )

        new_user.put()
        print 'Successfully created new user:' + user_email
        self.respond(user_email=user_email, status="Success")

class CreateAptService(ServiceHandler):
    def get(self):
        apt_id = uuid.uuid4()
        # req_json = json.loads(self.request.body)

        # apt_name = req_json[IDENTIFIER_APT_NAME]
        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        # user_email_lst = req_json[IDENTIFIER_USER_EMAIL_LIST]
        user_emails = self.request.get(IDENTIFIER_USER_EMAIL_LIST)

        user_email_lst = user_emails.split(",")
        cover_url = None

        user_email_lst.insert(0, user_email)

        # get rid of empty entity
        print("user_email_lst before filtering" + str(user_email_lst))
        user_email_lst = filter(None, user_email_lst)
        print("user_email_lst after filtering" + str(user_email_lst))

        # print user_email_lst

        # if IDENTIFIER_APT_PHOTO in req_json:
        #     cover_url = req_json[IDENTIFIER_APT_PHOTO]

        # check whether all of these email are valid users
        for user in user_email_lst:
            print user
            # user = user.encode('utf8')
            users = User.query(User.user_email == user).fetch()
            print("query user result" + str(len(users)))
            if len(users) == 0:
                response = {}
                response['error'] = 'the email: ' + user + ' has not been registered'
                return self.respond(**response)
            if users[0].apt_id is not None:
                response = {}
                response['error'] = 'the email: ' + user + ' has already joined other apartment'
                return self.respond(**response)


        for user in user_email_lst:
            users = User.query(User.user_email == user).fetch()
            cur_user = users[0]
            cur_user.apt_id = str(apt_id)
            cur_user.put()

        note_book_id = uuid.uuid4()
        new_note_book = NoteBook(notebook_id = str(note_book_id),
                                 apt_id = str(apt_id))
        new_note_book.put()

        new_apt = Apartment(apt_id = str(apt_id),
                            apt_name = apt_name,
                            creater_email = user_email,
                            user_email_lst = user_email_lst,
                            cover_url = cover_url,
                            notebook_id = str(note_book_id),
                            total_cost = 0)
        new_apt.put()

        self.respond(apt_id = str(apt_id), status="Success")


# get apartment basic info -liuchg
class GetAptBasicInfoService(ServiceHandler):
     def get(self):
         apt_id = self.request.get(IDENTIFIER_APT_ID)
         apts = Apartment.query(Apartment.apt_id == apt_id).fetch()
         user_nickname_lst=[]
         if apts[0]:
            apt = apts[0]
            for user_email in apt.user_email_lst:
                users = User.query(User.user_email == user_email).fetch()
                user = users[0]
                user_nickname_lst.append(user.nick_name)
            self.respond(status="success", apt_id=apt.apt_id, apt_name=apt.apt_name, creater_email=apt.user_email_lst, user_email_lst=apt.user_email_lst, user_nickname_lst=user_nickname_lst)
         else:
            print("cannot find the apartment with id :" + apt_id)
            self.respond(status="fail", error_msg="cannot find the apartment with id :" + apt_id)

class CreateExpenseService(ServiceHandler):
    def get(self):
        expense_id = uuid.uuid4()
        # req_json = json.loads(self.request.body)

        # expense_name = req_json[IDENTIFIER_EXPENSE_NAME ]
        expense_name = self.request.get(IDENTIFIER_EXPENSE_NAME)
        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        # apt_name = req_json[IDENTIFIER_APT_NAME]
        apt_name = self.request.get(IDENTIFIER_APT_NAME)

        user_emails = self.request.get(IDENTIFIER_USER_LIST)
        user_email_lst = user_emails.split(",")

        target_apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        target_apt = None

        for apt in target_apt_lst:
            if user_email in apt.user_email_lst:
                target_apt = apt
                break
        if target_apt == None:
            response = {}
            response['error'] = 'the user: ' + user_email + ' is not valid for apt: ' + apt_name
            return self.respond(**response)


        user_email_lst.insert(0, user_email)


        # check whether this apt name is valid or not
        expense_lst = Expense.query(Expense.expense_name == expense_name)
        for expense in expense_lst:
            for user in user_email_lst:
                if user in expense.user_email_lst:
                    response = {}
                    response['error'] = 'the apartment name: ' + expense_name + ' has not been used for ' + user
                    return self.respond(**response)

        # check whether all of these email are valid users
        for user in user_email_lst:
            users = User.query(User.user_email == user).fetch()
            if len(users) == 0:
                response = {}
                response['error'] = 'the email: ' + user + ' has not been registered'
                return self.respond(**response)



        cover_url = None
        # if IDENTIFIER_APT_PHOTO in req_json:
        #     cover_url = req_json[IDENTIFIER_APT_PHOTO]


        new_expense = Expense(apt_id = target_apt.apt_id,
                              creater_email = user_email,
                              user_email_lst = user_email_lst,
                              cover_url = cover_url,
                              expense_name = expense_name,
                              total_cost = 0,
                              is_paid = False,
                              expense_id = str(expense_id ))

        target_apt.expense_id_lst.insert(0, str(expense_id))
        new_expense.put()
        target_apt.put()
        self.respond(expense_id = str(expense_id), status="Success")


class CreateItemService(ServiceHandler):
    def get(self):

        cover_url = None
        # if IDENTIFIER_ITEM_PHOTO in req_json:
        #     cover_url = req_json[IDENTIFIER_ITEM_PHOTO]

        item_id = uuid.uuid4()
        # req_json = json.loads(self.request.body)

        # item_name = req_json[IDENTIFIER_ITEM_NAME]
        item_name = self.request.get(IDENTIFIER_ITEM_NAME)

        # expense_name = req_json[IDENTIFIER_EXPENSE_NAME]
        expense_name = self.request.get(IDENTIFIER_EXPENSE_NAME)

        # buyer_email = req_json[IDENTIFIER_BUYER_EMAIL]
        buyer_email = self.request.get(IDENTIFIER_BUYER_EMAIL)

        # sharer_email_lst = req_json[IDENTIFIER_SHARER_LIST]
        sharer_emails = self.request.get(IDENTIFIER_SHARER_LIST)
        sharer_email_lst = sharer_emails.split(",")

        expense_lst = Expense.query(Expense.expense_name == expense_name)
        expense_id = None

        # total_cost = float(req_json[IDENTIFIER_TOTAL_COST])
        cost = self.request.get(IDENTIFIER_TOTAL_COST)
        total_cost = float(cost)


        target_expense = None


        for expense in expense_lst:
            if buyer_email in expense.user_email_lst:
                expense_id = expense.expense_id
                target_expense = expense
                break

        if expense_id == None:
            response = {}
            response['error'] = 'the buyer email: ' + buyer_email + ' is not valid for this expense/apartment'
            return self.respond(**response)

        new_item = Item(item_id = str(item_id),
                        item_name = item_name,
                        cover_url = cover_url,
                        expense_id = expense_id,
                        buyer_email = buyer_email,
                        sharer_email_lst = sharer_email_lst,
                        total_cost = total_cost
                        )
        new_item.put()
        target_expense.item_id_lst.insert(0, str(item_id))
        target_expense.put()


        self.respond(item_id_id = str(item_id), status="Success")


# I fixed the logic here - liuchg
class addUserToAptService(ServiceHandler):
    def get(self):

        # req_json = json.loads(self.request.body)

        # apt_name = req_json[IDENTIFIER_APT_NAME]
        apt_name = self.request.get(IDENTIFIER_APT_NAME)

        # # user_email = req_json[IDENTIFIER_USER_EMAIL]
        # user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        # new_email = req_json[IDENTIFIER_NEW_EMAIL]
        new_email = self.request.get(IDENTIFIER_NEW_EMAIL)

        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        target_apt = None

        if len(apt_lst)!=0:
            target_apt = apt_lst[0]



        # for apt in apt_lst:
        #     if user_email in apt.user_email_lst:
        #         target_apt = apt
        #         break
        user_lst = User.query(User.user_email == new_email).fetch()

        # if target_apt == None:
        #     response = {}
        #     response['error'] = 'the email: ' + user_email + ' has not been registered'
        #     return self.respond(**response)
        if len(user_lst) == 0:
            response = {}
            response['error'] = 'the new email: ' + new_email + ' has not been registered'
            return self.respond(**response)

        new_user = user_lst[0]

        if not new_user.apt_id is None:
            response = {}
            response['error'] = 'the user: ' + new_email + ' cannot be added'
            return self.respond(**response)

        new_user.apt_id = target_apt.apt_id
        if not new_email in target_apt.user_email_lst:
            target_apt.user_email_lst.insert(0, new_email)
            target_apt.put()
        new_user.put()

        self.respond(apt_id = target_apt.apt_id, status="Success")


class addUserToExpenseService(ServiceHandler):
    def get(self):

        # req_json = json.loads(self.request.body)
        # expense_name = req_json[IDENTIFIER_EXPENSE_NAME]
        expense_name = self.request.get(IDENTIFIER_EXPENSE_NAME)

        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)


        # new_sharer_email = req_json[IDENTIFIER_NEW_EMAIL]
        new_sharer_email = self.request.get(IDENTIFIER_NEW_EMAIL)



        target_expense = None

        expense_lst = Expense.query(Expense.expense_name == expense_name)

        for expense in expense_lst:
            if user_email in expense.user_email_lst:
                target_expense = expense
                break

        if target_expense == None:
            response = {}
            response['error'] = 'the expense: ' + expense_name + ' has not been created'
            return self.respond(**response)



        if not new_sharer_email in target_expense.user_email_lst:
            target_expense.user_email_lst.insert(0, new_sharer_email)

        target_expense.put()

        self.respond(expense_id = target_expense.expense_id,
                     new_user = new_sharer_email, status="Success")


class checkSingleExpenseService(ServiceHandler):
    def get(self):

        expense_name = self.request.get(IDENTIFIER_EXPENSE_NAME)
        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt

        if cur_apt == None:
            response = {}
            response['error'] = 'the apt: ' + apt_name + ' is not available for user: ' + user_email
            return self.respond(**response)

        expense_lst = Expense.query(Expense.expense_name == expense_name).fetch()
        cur_expense = None
        for expense in expense_lst:
            if expense.apt_id == cur_apt.apt_id:
                cur_expense = expense

        if cur_expense == None:
            response = {}
            response['error'] = 'the apt: ' + apt_name + ' does not have a expense named: ' + expense_name
            return self.respond(**response)
        if cur_expense.is_paid:
            response = {}
            response['error'] = 'the : ' + expense_name + ' has already been paid'
            return self.respond(**response)
        cur_expense.checkout()
        cur_apt.total_cost += cur_expense.total_cost
        cur_apt.put()


        user_info_lst = []
        for user_email in cur_apt.user_email_lst:
            users = User.query(User.user_email == user_email).fetch()
            user = users[0]
            user_info = {}
            user_info['email:'] = user_email
            user_info['nick_name'] = user.nick_name
            user_info['owe'] = user.cost
            user_info['owed'] = user.borrow
            user_info['balance'] = user.owe
            user_info_lst.append(user_info)



        self.respond(user_info_lst = user_info_lst, status="Success")

class checkAllExpenseService(ServiceHandler):
    def get(self):
        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()
        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt
        if cur_apt == None:
            response = {}
            response['error'] = 'the apt: ' + apt_name + ' is not available for user: ' + user_email
            return self.respond(**response)

        for expense_id in cur_apt.expense_id_lst:
            expense_lst = Expense.query(Expense.expense_id == expense_id).fetch()
            if len(expense_lst) > 0:
                expense = expense_lst[0]
                if not expense.is_paid:
                    expense.checkout()
                    cur_apt.total_cost += expense.total_cost
                    cur_apt.put()

        self.respond(status="Success")


class getPaymentService(ServiceHandler):
    def get(self):
        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        # print "called: " + user_email + ", " + apt_name
        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt

        user_lst = User.query(User.apt_id == cur_apt.apt_id).fetch()

        sorted_user_lst = sorted(user_lst, key=lambda user:user.owe)

        first = 0
        end = len(sorted_user_lst) - 1

        payment_lst = []

        print "sorted_lst: " + str(sorted_user_lst)

        while first < end:
            first_user = sorted_user_lst[first]
            end_user = sorted_user_lst[end]
            if first_user.owe == 0:
                first += 1
                continue
            if end_user.owe == 0:
                end -= 1
                continue
            payment = {}

            payment['from'] = first_user.user_email
            payment['to'] = end_user.user_email



            if abs(first_user.owe) > end_user.owe:
                payment['amount'] = end_user.owe
                first_user.owe += end_user.owe
                end_user.owe = 0

            else:
                payment['amount'] = abs(first_user.owe)
                end_user.owe -= abs(first_user.owe)
                first_user.owe = 0


            print payment
            print first_user.user_email + ": " + str(first_user.owe)
            print end_user.user_email + ": " + str(end_user.owe)

            payment_lst.append(payment)
            first_user.put()
            end_user.put()

        self.respond(payment_lst = payment_lst, status="Success")



class addNoteService(ServiceHandler):
    def get(self):

        # req_json = json.loads(self.request.body)
        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        # apt_name = req_json[IDENTIFIER_APT_NAME]
        apt_name =  self.request.get(IDENTIFIER_APT_NAME)
        # description = req_json[IDENTIFIER_DESCRIPTION_NAME]
        description = self.request.get(IDENTIFIER_DESCRIPTION_NAME)

        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt

        if cur_apt == None:
            response = {}
            response['error'] = 'the apt: ' + apt_name + ' is not available for user: ' + user_email
            return self.respond(**response)

        cur_note_book_id = cur_apt.notebook_id

        cur_note_book_lst = NoteBook.query(NoteBook.notebook_id == cur_note_book_id).fetch()

        if len(cur_note_book_lst) == 0:
            response = {}
            response['error'] = 'we dont have notebook for the apt: ' + apt_name
            return self.respond(**response)

        cur_note_book = cur_note_book_lst[0]

        note_id = uuid.uuid4()
        note = Note(id = str(note_id), description = description, author_email = user_email, notebook_id = cur_note_book_id)

        cur_note_book.note_id_lst.append(str(note_id))

        cur_note_book.put()
        note.put()

        self.respond(note_id = str(note_id), notebook_id = cur_note_book_id, status="Success")



class editNoteService(ServiceHandler):
    def get(self):

        # req_json = json.loads(self.request.body)
        # user_email = req_json[IDENTIFIER_USER_EMAIL]
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        # note_id = req_json[IDENTIFIER_NOTE_ID]
        note_id = self.request.get(IDENTIFIER_NOTE_ID)
        # new_description = req_json[IDENTIFIER_NEW_DESCRIPTION_NAME]
        new_description = self.request.get(IDENTIFIER_NEW_DESCRIPTION_NAME)

        cur_note_lst = Note.query(Note.id == note_id).fetch()

        if len(cur_note_lst) == 0:
            response = {}
            response['error'] = 'the note with id : ' + note_id + ' is valid'
            return self.respond(**response)

        cur_note = cur_note_lst[0]

        if user_email != cur_note.author_email:
            response = {}
            response['error'] = 'you cannot edit this note'
            return self.respond(**response)

        cur_note.description = new_description
        cur_note.put()

        self.respond(status="Success")

class getAllNoteService(ServiceHandler):
    def get(self):
        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        # print "called: " + user_email + ", " + apt_name
        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt

        cur_notebook_lst = NoteBook.query( NoteBook.notebook_id == cur_apt.notebook_id).fetch()
        if len(cur_notebook_lst) == 0:
            response = {}
            response['error'] = 'we dont have notebook for the apt: ' + apt_name
            return self.respond(**response)


        cur_notebook = cur_notebook_lst[0]


        retList = []
        for noteid in cur_notebook.note_id_lst:
            note_lst = Note.query(Note.id == noteid).fetch()
            cur_note = note_lst[0]
            ret_note = {}
            ret_note['author'] = cur_note.author_email
            ret_note['description'] = cur_note.description
            date = str(cur_note.date)
            ret_note['last_edit_date'] = date
            retList.append(ret_note)

        self.respond(AllNoteLst = retList, status="Success")



class getSingleNoteService(ServiceHandler):
    def get(self):

        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        note_id = self.request.get(IDENTIFIER_NOTE_ID)

        cur_note_lst = Note.query(Note.id == note_id).fetch()

        if len(cur_note_lst) == 0:
            response = {}
            response['error'] = 'The ID is not available: ' + note_id
            return self.respond(**response)

        cur_note = cur_note_lst[0]

        retValue = {}
        retValue['author'] = cur_note.author_email
        retValue['last_edit_date'] = str(cur_note.date)
        retValue['description'] = cur_note.description
        self.respond(Note = retValue, status="Success")

class getOweandOwedService(ServiceHandler):
    def get(self):

        apt_name = self.request.get(IDENTIFIER_APT_NAME)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)
        apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()

        # print "called: " + user_email + ", " + apt_name
        cur_apt = None
        for apt in apt_lst:
            if user_email in apt.user_email_lst:
                cur_apt = apt

        user_info_lst = []
        for user_email in apt.user_email_lst:
            users = User.query(User.user_email == user_email).fetch()
            user = users[0]
            user_info = {}
            user_info['email:'] = user_email
            user_info['nick_name'] = user.nick_name
            user_info['owe'] = user.cost
            user_info['owed'] = user.borrow
            user_info['balance'] = user.owe
            user_info_lst.append(user_info)

        self.respond(user_info_lst = user_info_lst, total_cost = apt.total_cost, status="Success")


class getUserInfoService(ServiceHandler):
    def get(self):
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        users = User.query(User.user_email == user_email).fetch()
        if len(users) == 0:
            response = {}
            response['error'] = 'the email: ' + user_email + ' has not registered yet'
            return self.respond(**response)

        cur_user = users[0]
        bank_account = cur_user.bank_account
        nick_name = cur_user.nick_name
        owe = cur_user.cost
        owed = cur_user.borrow
        balance = cur_user.owe

        print("user information collected. e.g. bankaccount="+bank_account)

        tasks = cur_user.getAlltasks()
        finished_task_lst = []
        unfinished_task_lst = []

        for task in tasks:
            cur_task = {}
            cur_task['task_id'] = task.task_id
            cur_task['task_name'] = task.task_name
            if task.finished:
                finished_task_lst.append(cur_task)
            else:
                unfinished_task_lst.append(cur_task)

        taskinfo = {}
        taskinfo['finished_task_lst'] = finished_task_lst
        taskinfo['unfinished_task_lst'] = unfinished_task_lst

        print("task collected")

        apt_id = cur_user.apt_id

        apts = Apartment.query(Apartment.apt_id == apt_id).fetch()

        apt_info = {}
        if len(apts) > 0:
            apt = apts[0]
            apt_info['apt_name'] = apt.apt_name
            apt_info['apt_id'] = apt.apt_id
            apt_info['roommates_lst'] = apt.get_all_memebers_nickname()
            apt_info['apt_photo'] = apt.cover_url

        # usr_photo = cur_user.cover_url

        print("apartment information collected. now respond.")

        self.respond(status="Success", bank_account=bank_account, nick_name = nick_name,
                     user_email = user_email, owe=owe, owed = owed, balance = balance, apt_info = apt_info,
                     task_info = taskinfo, registered=True)


class getAptInfoService(ServiceHandler):
        def get(self):
            user_email = self.request.get(IDENTIFIER_USER_EMAIL)
            apt_name = self.request.get(IDENTIFIER_APT_NAME)

            apt_lst = Apartment.query(Apartment.apt_name == apt_name).fetch()
            cur_apt = None
            for apt in apt_lst:
                if user_email in apt.user_email_lst:
                    cur_apt = apt
            if cur_apt == None:
                response = {}
                response['error'] = 'the apt: ' + apt_name + ' is not available for user: ' + user_email
                return self.respond(**response)

            apt_name = cur_apt.apt_name
            roomates_nickname_lst = cur_apt.get_all_memebers_nickname()
            roomates_email_lst = cur_apt.user_email_lst
            apt_id = cur_apt.apt_id
            cover_url = cur_apt.cover_url

            note_lst = []
            notebook = cur_apt.get_Note_book()
            notes_lst = notebook.getAllnotes()

            for note in notes_lst:
                cur_note = {}
                cur_note['id'] = str(note.id)
                cur_note['description'] = note.description
                author_email = note.author_email
                authors = User.query(User.user_email == author_email).fetch()
                author = authors[0]
                writer = author.nick_name
                cur_note['writer'] = writer
                cur_note['date'] = str(note.date)
                note_lst.append(cur_note)
            expenses_lst = []

            expenses = cur_apt.getAllexpenses()

            for expense in expenses:
                cur_expense = {}
                cur_expense['expense_id'] = str(expense.expense_id)
                creater_email = expense.creater_email
                creaters = User.query(User.user_email == creater_email).fetch()
                creater = creaters[0]
                creater_nick_name = creater.nick_name
                cur_expense['creater_nickname'] = creater_nick_name
                cur_expense['photo'] = expense.cover_url
                cur_expense['date'] = str(expense.last_edit)
                cur_expense['expense_name'] = expense.expense_name
                cur_expense['sharer_lst'] = expense.user_email_lst
                cur_expense['is_paid'] = expense.is_paid
                cur_expense['the_number_of_items'] = len(expense.item_id_lst)
                expenses_lst.append(cur_expense)


            self.respond(roomates_email_lst = roomates_email_lst,
                         roomates_nickname_lst = roomates_nickname_lst,
                         apt_id = str(apt_id),
                         apt_name = apt_name,
                         cover_url = cover_url,
                         notes_lst = note_lst,
                         expenses_lst = expenses_lst,
                         status="Success")

# Added by liuchg
class getExpenseListService(ServiceHandler):
    def get(self):
        apt_id = self.request.get(IDENTIFIER_APT_ID)
        print "getExpenseListService, apt_id="+apt_id
        expenses_lst = []
        apt_lst = Apartment.query(Apartment.apt_id == apt_id).fetch()
        if len(apt_lst)!=0 :
            apt = apt_lst[0]
            expenses = apt.getAllexpenses()
            if len(expenses)!=0:
                for expense in expenses:
                    cur_expense = {}
                    cur_expense['expense_id'] = str(expense.expense_id)
                    creater_email = expense.creater_email
                    creaters = User.query(User.user_email == creater_email).fetch()
                    creater = creaters[0]
                    creater_nick_name = creater.nick_name
                    cur_expense['creater_nickname'] = creater_nick_name
                    cur_expense['photo'] = expense.cover_url
                    cur_expense['date'] = str(expense.last_edit)
                    cur_expense['expense_name'] = expense.expense_name
                    cur_expense['sharer_lst'] = expense.user_email_lst
                    cur_expense['is_paid'] = expense.is_paid
                    cur_expense['the_number_of_items'] = len(expense.item_id_lst)
                    cur_expense['total_cost'] = expense.total_cost
                    # cur_expense['approval_cost'] = expense.approval_cost
                    expenses_lst.append(cur_expense)
        self.respond(status="success", expenses_lst=expenses_lst)


class getExpenseInfoService(ServiceHandler):
        def get(self):

            expense_id = self.request.get(IDENTIFIER_EXPENSE_ID)

            print "expense_id :" + expense_id

            expenses = Expense.query(Expense.expense_id == expense_id).fetch()
            expense = expenses[0]
            expense_name = expense.expense_name
            items = expense.getAllItems()
            tasks = expense.getAllTasks()
            expected_cost = 0.0
            items_lst = []
            is_paid = expense.is_paid
            expense_user_lst = expense.getUserNickNameLst()
            for item in items:
                expected_cost += item.total_cost
                cur_item = {}
                cur_item['item_cost'] = item.total_cost
                cur_item['is_paid'] = item.is_paid
                cur_item['item_id'] = str(item.item_id)
                cur_item['cover_url'] = item.cover_url
                cur_item['buyer'] = item.getBuyer()
                cur_item['sharer_lst'] = item.getSharersNickName()
                cur_item['sharer_email_lst'] = item.sharer_email_lst
                cur_item['item_name'] = item.item_name
                cur_item['expense_id'] = item.expense_id    # fixed ; there was no expense_id attached here
                cur_item['buyer_email'] = item.buyer_email
                items_lst.append(cur_item)

            finished_tasks_lst = []
            unassigned_tasks_lst = []
            assigned_tasks_lst = []

            for task in tasks:
                cur_task = {}
                cur_task['photo'] = task.cover_url
                cur_task['creater'] = task.getCreaterNickName()
                cur_task['creater_email'] = task.creater_email
                cur_task['task_name'] = task.task_name
                cur_task['task_id'] = str(task.task_id)
                if task.assigned:
                    cur_task['person in charge'] = task.getChargerNickName()
                    cur_task['person in charge email'] = task.charger_email
                    if task.finished:
                        finished_tasks_lst.append(cur_task)
                    else:
                        assigned_tasks_lst.append(cur_task)
                else:
                    unassigned_tasks_lst.append(cur_task)

            task_info = {}
            task_info['finished_tasks_lst'] = finished_tasks_lst
            task_info['unassigned_tasks_lst'] = unassigned_tasks_lst
            task_info['assigned_tasks_lst'] = assigned_tasks_lst

            user_email_lst=expense.user_email_lst

            self.respond(total_cost = expected_cost, items_lst = items_lst, is_paid = is_paid,
                         expense_name = expense_name, expense_user_lst = expense_user_lst, user_email_lst=user_email_lst,
                         task_info = task_info, status = 'Success')



class getItemInfoService(ServiceHandler):
        def get(self):
            item_id = self.request.get(IDENTIFIER_ITEM_ID)
            print "111111111111111121111"
            print item_id
            items = Item.query(Item.item_id == item_id).fetch()
            item = items[0]

            cur_item = {}
            cur_item['item_cost'] = item.total_cost
            cur_item['is_paid'] = item.is_paid
            cur_item['item_id'] = str(item.item_id)
            cur_item['cover_url'] = item.cover_url
            cur_item['buyer'] = item.getBuyer()
            cur_item['sharer_lst'] = item.getSharersNickName()
            cur_item['item_name'] = item.item_name

            self.respond(item = cur_item, status = 'Success')


class addReplyService(ServiceHandler):
        def get(self):
            # req_json = json.loads(self.request.body)
            # note_id = req_json[IDENTIFIER_NOTE_ID]
            note_id = self.request.get(IDENTIFIER_NOTE_ID)
            # user_email = req_json[IDENTIFIER_USER_EMAIL]
            user_email = self.request.get(IDENTIFIER_USER_EMAIL)
            # description = req_json[IDENTIFIER_DESCRIPTION_NAME]
            description = self.request.get(IDENTIFIER_DESCRIPTION_NAME)

            reply_id = uuid.uuid4()
            notes = Note.query(Note.id == note_id).fetch()
            note = notes[0]

            user_lst = User.query(User.user_email == user_email).fetch()
            user = user_lst[0]

            new_reply = Reply(author_email = user_email,
                              note_id = str(note_id),
                              reply_id = str(reply_id),
                              description = description,
                              nick_name = user.nick_name
                              )
            new_reply.put()
            note.reply_id_lst.append(str(reply_id))
            note.put()

            self.respond(reply_id = str(reply_id),
                         status="Success")


class getAllReplyService(ServiceHandler):
    def get(self):
        note_id = self.request.get(IDENTIFIER_NOTE_ID)
        notes = Note.query(Note.id == note_id).fetch()
        note = notes[0]

        replys = note.getAllreply()
        reply_lst = []

        sorted_replys = sorted(replys, key=lambda reply:reply.date)

        for reply in sorted_replys:
            cur_reply = {}
            cur_reply['author'] = reply.nick_name
            cur_reply['author_email'] = reply.author_email
            cur_reply['description'] = reply.description
            cur_reply['reply_id'] = str(reply.reply_id)
            cur_reply['date'] = str(reply.date)
            reply_lst.append(cur_reply)

        self.respond(reply_lst = reply_lst,
                         status="Success")




class createTaskService(ServiceHandler):
    def get(self):

        photo = None
        # if IDENTIFIER_TASK_PHOTO in req_json:
        #     photo = req_json[IDENTIFIER_TASK_PHOTO]


        task_id = uuid.uuid4()

        # req_json = json.loads(self.request.body)

        # task_name = req_json[IDENTIFIER_TASK_NAME]
        task_name = self.request.get(IDENTIFIER_TASK_NAME)

        # expense_id = req_json[IDENTIFIER_EXPENSE_ID]
        expense_id = self.request.get(IDENTIFIER_EXPENSE_ID)

        # creater_email = req_json[IDENTIFIER_USER_EMAIL]
        creater_email = self.request.get(IDENTIFIER_USER_EMAIL)

        # candidate_lst= req_json[IDENTIFIER_USER_EMAIL_LIST]
        candidates = self.request.get(IDENTIFIER_USER_EMAIL_LIST)
        candidate_lst = candidates.split(",")

        # description = req_json[IDENTIFIER_DESCRIPTION_NAME]
        description = self.request.get(IDENTIFIER_DESCRIPTION_NAME)

        candidate_lst.append(creater_email)
        expenses = Expense.query(Expense.expense_id == expense_id).fetch()
        expense = expenses[0]
        expense.task_id_lst.append(str(task_id))
        expense.put()
        new_task = Task(task_name = task_name, expense_id = expense_id, creater_email = creater_email,
                        candidate_lst = candidate_lst, description = description, cover_url = photo, task_id = str(task_id),
                        finished = False, assigned = False)
        new_task.put()

        self.respond(task_id = str(task_id),
                         status="Success")

class pickTaskService(ServiceHandler):
    def get(self):
        task_id = self.request.get(IDENTIFIER_TASK_ID)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        tasks = Task.query(Task.task_id == task_id).fetch()
        task = tasks[0]

        if not user_email in task.candidate_lst:
            response = {}
            response['error'] = 'the email: ' + user_email + ' is not valid for this task'
            return self.respond(**response)

        users = User.query(User.user_email == user_email).fetch()
        user = users[0]
        user.tasks_list.append(task_id)
        user.put()
        task.assigned = True
        task.charger_email = user_email
        task.put()

        self.respond(status="Success")

class finishTaskService(ServiceHandler):
    def get(self):
        task_id = self.request.get(IDENTIFIER_TASK_ID)
        total_cost = self.request.get(IDENTIFIER_TOTAL_COST)
        user_email = self.request.get(IDENTIFIER_USER_EMAIL)

        total_cost = float(total_cost)

        tasks = Task.query(Task.task_id == task_id).fetch()
        task = tasks[0]

        if task.finished:
            response = {}
            response['error'] = 'the task has already been finished'
            return self.respond(**response)
        if user_email != task.charger_email:
            response = {}
            response['error'] = 'the task has been assigned to other roommate'
            return self.respond(**response)
        task.finished = True
        task.put()
        item_id = str(uuid.uuid4())
        sharer_lst = task.candidate_lst
        sharer_lst.remove(task.charger_email)



        new_Item = Item(item_id = item_id, cover_url = task.cover_url, expense_id = task.expense_id,
                        total_cost = total_cost,
                        buyer_email = task.charger_email,
                        sharer_email_lst = sharer_lst,
                        item_name = task.task_name)

        new_Item.put()

        self.respond(item_name = task.task_name, item_id = task.task_id, status="Success")


class getAllTaskService(ServiceHandler):
    def get(self):
        expense_id = self.request.get(IDENTIFIER_EXPENSE_ID)
        expenses = Expense.query(Expense.expense_id == expense_id).fetch()
        expense = expenses[0]

        unassigned_tasks_lst = []
        assigned_tasks_lst = []
        finished_tasks_lst = []

        tasks = expense.getAllTasks()

        for task in tasks:
            cur_task = {}
            cur_task['photo'] = task.cover_url
            cur_task['creater'] = task.getCreaterNickName()
            cur_task['creater_email'] = task.creater_email
            cur_task['task_name'] = task.task_name
            cur_task['task_id'] = str(task.task_id)
            if task.assigned:
                cur_task['person in charge'] = task.getChargerNickName()
                cur_task['person in charge email'] = task.charger_email
                if task.finished:
                    finished_tasks_lst.append(cur_task)
                else:
                    assigned_tasks_lst.append(cur_task)
            else:
                unassigned_tasks_lst.append(cur_task)

        task_info = {}
        task_info['finished_tasks_lst'] = finished_tasks_lst
        task_info['unassigned_tasks_lst'] = unassigned_tasks_lst
        task_info['assigned_tasks_lst'] = assigned_tasks_lst

        self.respond(task_info=task_info, status="Success")

def removeQuote(str):
    str.replace('"','')
    return str


app = webapp2.WSGIApplication([
    ('/getUserInfo', getUserInfoService),
    ('/createAccount', CreateAccountService),
    ('/createApt', CreateAptService),
    ('/getBasicAptInfo', GetAptBasicInfoService), #newly added
    ('/getExpenseList', getExpenseListService), #newly added
    ('/getAptInfo', getAptInfoService),
    ('/createExpense', CreateExpenseService),
    ('/getExpenseInfo', getExpenseInfoService),
    ('/createItem', CreateItemService),
    ('/getItemInfo', getItemInfoService),

    ('/addReply', addReplyService),
    ('/getAllReply', getAllReplyService),

    ('/createTask', createTaskService),
    ('/pickTask', pickTaskService),
    ('/finishTask', finishTaskService),
    ('/getAllTask', getAllTaskService),

    ('/addUserToExpense', addUserToExpenseService),
    ('/addUserToApt', addUserToAptService),
    ('/checkSingleExpense',checkSingleExpenseService),
    ('/checkAllExpense', checkAllExpenseService),
    ('/getPayment', getPaymentService),
    ('/getOweandOwed', getOweandOwedService),
    ('/addNote', addNoteService),
    ('/editNote' ,editNoteService),
    ('/getAllNote', getAllNoteService),
    ('/getSingleNote', getSingleNoteService)
], debug=True)
