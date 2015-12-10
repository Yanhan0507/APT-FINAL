__author__ = 'henry'



from google.appengine.ext import ndb
import uuid
import webapp2, json

class Expense(ndb.Model):
    apt_id = ndb.StringProperty()
    creater_email = ndb.StringProperty()
    user_email_lst = ndb.StringProperty(repeated=True)
    item_id_lst = ndb.StringProperty(repeated=True)
    is_paid = ndb.BooleanProperty()
    expense_id = ndb.StringProperty()
    expense_name = ndb.StringProperty()
    cover_url = ndb.StringProperty()
    last_edit = ndb.DateTimeProperty(auto_now_add=True)
    total_cost = ndb.FloatProperty()
    approval_cost = ndb.FloatProperty()

    def checkout(self):
        for item_id in self.item_id_lst:
            item_lst = Item.query(Item.item_id == item_id).fetch()
            if len(item_lst) > 0:
                for item in item_lst:
                    if item.is_paid:
                        continue
                    item.checkout()
                    self.total_cost += item.total_cost

        self.is_paid = True
        self.put()
    # def checkOutSingleItem(self, item_id):

class NoteBook(ndb.Model):
    notebook_id = ndb.StringProperty()
    apt_id = ndb.StringProperty()
    note_id_lst = ndb.StringProperty(repeated=True)

    def addNote(self, author_id, description):
        note_id = uuid.uuid4()
        new_note = Note(author_id = author_id,
                        description = description,
                        id = note_id
                        )
        new_note.put()
        self.note_id_lst.insert(0, new_note)

class Note(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)
    author_email = ndb.StringProperty()
    description = ndb.StringProperty()
    id = ndb.StringProperty()
    notebook_id = ndb.StringProperty()

    def show(self):
        author_lst = User.query(User.user_email == self.author_email)
        author_name = None
        if len(author_lst) > 0:
            author = author_lst[0]
            author_name = author.nick_name
        if author_name:
            dict["author_name"] = author_name
        dict["description"] = self.description
        dict["last_edit_time"] = self.date





class Item(ndb.Model):
    item_id = ndb.StringProperty()
    is_paid = ndb.BooleanProperty()
    expense_id = ndb.StringProperty()
    item_name = ndb.StringProperty()
    buyer_email = ndb.StringProperty()
    total_cost = ndb.FloatProperty()
    sharer_email_lst = ndb.StringProperty(repeated=True)
    cover_url = ndb.StringProperty()

    def checkout(self):
        num_of_user = len(self.sharer_email_lst) + 1
        payment = self.total_cost/num_of_user


        buyer_lst = User.query(User.user_email == self.buyer_email).fetch()
        buyer = buyer_lst[0]
        buyer.borrow += payment
        buyer.cost += self.total_cost
        for sharer_email in self.sharer_email_lst:
            sharer_lst = User.query(User.user_email == sharer_email).fetch()

            if len(sharer_lst) == 0:
                continue
            sharer = sharer_lst[0]
            sharer.owe -=  payment
            buyer.owe += payment
            sharer.borrow += payment
            sharer.put()
        buyer.put()
        self.is_paid = True
        self.put()




class Apartment(ndb.Model):
    creater_email = ndb.StringProperty()
    notebook_id = ndb.StringProperty()
    apt_name = ndb.StringProperty()
    apt_id = ndb.StringProperty()
    user_email_lst = ndb.StringProperty(repeated=True)
    expense_id_lst = ndb.StringProperty(repeated=True)
    cover_url = ndb.StringProperty()
    total_cost = ndb.FloatProperty()

    def checkout_single_expense(self, expense_id):
        if expense_id in self.expense_id_lst:
            current_expense_lst = Expense.query(Expense.expense_id == expense_id)
            if len(current_expense_lst) > 0:
                current_expense = current_expense_lst[0]
                if not current_expense.is_paid:
                    current_expense.checkout()
        self.put()


    def checkout_all_expense(self):
        for expense_id in self.expense_id_lst:
            self.checkout_single_expense(expense_id)
        self.put()


class User(ndb.Model):
     apt_id = ndb.StringProperty()
     nick_name = ndb.StringProperty()
     user_email = ndb.StringProperty()
     bank_account = ndb.StringProperty()

     cost = ndb.FloatProperty()     # the money I paid for others
     borrow = ndb.FloatProperty()   # the money others paid for me

     owe = ndb.FloatProperty()
     cover_url = ndb.StringProperty()
     todo_list = ndb.StringProperty(repeated=True)


# class payment(ndb.Model):
#     from_email = ndb.StringProperty()
#     to_email = ndb.StringProperty()
#     amount = ndb.FloatProperty()
#     is_paid = ndb.BooleanProperty()
#     payment_id = ndb.StringProperty()








