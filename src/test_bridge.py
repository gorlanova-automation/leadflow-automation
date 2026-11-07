import unittest
from unittest.mock import patch
import bridge

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.hook='https://crm.example.com/rest/1/syntheticTestKey/'
        self.body={'request_id':'demo-guard-001','category_id':17,'demo':True,
                   'name':'Тест','email':'test@example.com','message':'Учебная заявка'}
    def test_scope_guard_prevents_network(self):
        for mutation in ({'category_id':0},{'demo':False},{'request_id':'../crm.delete'}):
            with self.subTest(mutation=mutation),patch('bridge.call') as api:
                result=bridge.dispatch('/deal/create',self.hook,self.body|mutation)
                self.assertFalse(result['ok']); api.assert_not_called()
    def test_arbitrary_host_and_method_prevent_network(self):
        with patch('bridge.call') as api:
            self.assertFalse(bridge.dispatch('/deal/create','https://evil.invalid/',self.body)['ok'])
            self.assertFalse(bridge.dispatch('/crm.deal.delete',self.hook,self.body)['ok'])
            api.assert_not_called()
    def test_existing_deal_never_created_again(self):
        with patch('bridge.call',return_value=[{'ID':'999','CATEGORY_ID':'17'}]) as api:
            self.assertEqual(bridge.dispatch('/deal/create',self.hook,self.body)['deal_id'],999)
            self.assertEqual(api.call_count,1)
            self.assertEqual(api.call_args.args[1],'crm.deal.list')
    def test_ambiguous_create_only_reconciles(self):
        with patch('bridge.call',side_effect=[[],bridge.Upstream('upstream_unavailable'),[]]) as api:
            result=bridge.dispatch('/deal/create',self.hook,self.body)
            self.assertEqual(result['error'],'ambiguous_create')
            self.assertEqual([c.args[1] for c in api.call_args_list],['crm.deal.list','crm.deal.add','crm.deal.list'])
    def test_fields_cannot_be_overridden(self):
        with patch('bridge.call',side_effect=[[],999]) as api:
            bridge.dispatch('/deal/create',self.hook,self.body|{'fields':{'CATEGORY_ID':0},'message':'<script>x</script>'})
            fields=api.call_args.args[2]['fields']
            self.assertEqual(fields['CATEGORY_ID'],17)
            self.assertNotIn('<script>',fields['COMMENTS'])
            self.assertNotIn('CONTACT_ID',fields)
    def test_non_demo_email_not_created(self):
        with patch('bridge.call',return_value=[]) as api:
            result=bridge.dispatch('/deal/create',self.hook,self.body|{'email':'person@real.invalid'})
            self.assertEqual(result['error'],'demo_email_required')
            self.assertEqual(api.call_count,1)

if __name__=='__main__': unittest.main(verbosity=2)
