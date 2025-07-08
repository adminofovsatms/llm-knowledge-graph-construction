from flask import Flask, request, jsonify
import os
import json

# Import all your modules
try:
    import createbill
    import createBillCompanywise
    import createcompany
    import createCreditNotes
    import createCusomterPayments
    import createCustomer
    import createInvoice
    import createproduct
    import createrefund
    import createvendor
    import createVendorPayments
    import deletebill
    import deletecompany
    import deletevendor
    import modifybill
    import modifyvendor
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

app = Flask(__name__)

# Home endpoint with API documentation
@app.route('/')
def home():
    endpoints = {
        "message": "Business Management API",
        "available_endpoints": {
            "Create Operations": {
                "/api/create/bill": "POST - Create bill",
                "/api/create/bill-company": "POST - Create bill by company",
                "/api/create/company": "POST - Create company",
                "/api/create/credit-notes": "POST - Create credit notes",
                "/api/create/customer-payments": "POST - Create customer payments",
                "/api/create/customer": "POST - Create customer",
                "/api/create/invoice": "POST - Create invoice",
                "/api/create/product": "POST - Create product",
                "/api/create/refund": "POST - Create refund",
                "/api/create/vendor": "POST - Create vendor",
                "/api/create/vendor-payments": "POST - Create vendor payments"
            },
            "Delete Operations": {
                "/api/delete/bill": "DELETE - Delete bill",
                "/api/delete/company": "DELETE - Delete company",
                "/api/delete/vendor": "DELETE - Delete vendor"
            },
            "Modify Operations": {
                "/api/modify/bill": "PUT - Modify bill",
                "/api/modify/vendor": "PUT - Modify vendor"
            }
        }
    }
    return jsonify(endpoints)

# Create Operations
@app.route('/api/create/bill', methods=['POST'])
def create_bill():
    try:
        data = request.json or {}
        result = createbill.main(data) if hasattr(createbill, 'main') else createbill.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/bill-company', methods=['POST'])
def create_bill_company():
    try:
        data = request.json or {}
        result = createBillCompanywise.main(data) if hasattr(createBillCompanywise, 'main') else createBillCompanywise.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/company', methods=['POST'])
def create_company():
    try:
        data = request.json or {}
        result = createcompany.main(data) if hasattr(createcompany, 'main') else createcompany.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/credit-notes', methods=['POST'])
def create_credit_notes():
    try:
        data = request.json or {}
        result = createCreditNotes.main(data) if hasattr(createCreditNotes, 'main') else createCreditNotes.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/customer-payments', methods=['POST'])
def create_customer_payments():
    try:
        data = request.json or {}
        result = createCusomterPayments.main(data) if hasattr(createCusomterPayments, 'main') else createCusomterPayments.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/customer', methods=['POST'])
def create_customer():
    try:
        data = request.json or {}
        result = createCustomer.main(data) if hasattr(createCustomer, 'main') else createCustomer.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.json or {}
        result = createInvoice.main(data) if hasattr(createInvoice, 'main') else createInvoice.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/product', methods=['POST'])
def create_product():
    try:
        data = request.json or {}
        result = createproduct.main(data) if hasattr(createproduct, 'main') else createproduct.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/refund', methods=['POST'])
def create_refund():
    try:
        data = request.json or {}
        result = createrefund.main(data) if hasattr(createrefund, 'main') else createrefund.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/vendor', methods=['POST'])
def create_vendor():
    try:
        data = request.json or {}
        result = createvendor.main(data) if hasattr(createvendor, 'main') else createvendor.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create/vendor-payments', methods=['POST'])
def create_vendor_payments():
    try:
        data = request.json or {}
        result = createVendorPayments.main(data) if hasattr(createVendorPayments, 'main') else createVendorPayments.create(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Delete Operations
@app.route('/api/delete/bill', methods=['DELETE'])
def delete_bill():
    try:
        data = request.json or {}
        result = deletebill.main(data) if hasattr(deletebill, 'main') else deletebill.delete(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete/company', methods=['DELETE'])
def delete_company():
    try:
        data = request.json or {}
        result = deletecompany.main(data) if hasattr(deletecompany, 'main') else deletecompany.delete(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete/vendor', methods=['DELETE'])
def delete_vendor():
    try:
        data = request.json or {}
        result = deletevendor.main(data) if hasattr(deletevendor, 'main') else deletevendor.delete(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Modify Operations
@app.route('/api/modify/bill', methods=['PUT'])
def modify_bill():
    try:
        data = request.json or {}
        result = modifybill.main(data) if hasattr(modifybill, 'main') else modifybill.modify(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/modify/vendor', methods=['PUT'])
def modify_vendor():
    try:
        data = request.json or {}
        result = modifyvendor.main(data) if hasattr(modifyvendor, 'main') else modifyvendor.modify(data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Business Management API is running'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)